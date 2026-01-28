import pandas as pd
from sqlalchemy import create_engine, text, inspect
import logging
from typing import Dict, List, Optional
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

class DataSourceManager:
    """Manage dynamic data sources (CSV uploads, database connections)"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.inspector = inspect(self.engine)
        self._initialize_metadata_table()
    
    def _initialize_metadata_table(self):
        """Create table to track uploaded data sources"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS data_sources (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    table_name TEXT NOT NULL UNIQUE,
                    source_type TEXT NOT NULL,
                    row_count INTEGER,
                    column_count INTEGER,
                    columns JSONB,
                    uploaded_at TIMESTAMP DEFAULT NOW(),
                    description TEXT
                )
            """))
            conn.commit()
    
    def clean_column_name(self, col: str) -> str:
        """Convert column names to database-friendly format"""
        col = col.lower().strip()
        col = col.replace(' ', '_')
        col = col.replace('-', '_')
        col = col.replace('/', '_')
        col = col.replace('.', '_')
        col = ''.join(c for c in col if c.isalnum() or c == '_')
        # Ensure doesn't start with number
        if col and col[0].isdigit():
            col = 'col_' + col
        return col or 'unnamed_column'
    
    def upload_csv(self, df: pd.DataFrame, table_name: str, description: str = "") -> Dict:
        """Upload CSV data to database"""
        try:
            # Clean column names
            original_columns = df.columns.tolist()
            df.columns = [self.clean_column_name(col) for col in df.columns]
            
            # Handle duplicates
            seen = {}
            new_cols = []
            for col in df.columns:
                if col in seen:
                    seen[col] += 1
                    new_cols.append(f"{col}_{seen[col]}")
                else:
                    seen[col] = 0
                    new_cols.append(col)
            df.columns = new_cols
            
            cleaned_columns = df.columns.tolist()
            
            logger.info(f"Uploading CSV to table: {table_name}")
            logger.info(f"Original columns: {original_columns}")
            logger.info(f"Cleaned columns: {cleaned_columns}")
            
            # Create engine with autocommit
            from sqlalchemy import create_engine
            import json
            
            engine = create_engine(self.engine.url, isolation_level="AUTOCOMMIT")
            
            # Drop existing table if exists
            with engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                logger.info(f"Dropped old table if existed: {table_name}")
            
            # Load data to new table
            df.to_sql(
                table_name,
                engine,
                if_exists='replace',
                index=False,
                chunksize=1000
            )
            
            logger.info(f"Created table and loaded {len(df)} rows")
            
            # Grant permissions
            with engine.connect() as conn:
                try:
                    result = conn.execute(text(f"SELECT to_regclass('{table_name}')"))
                    table_exists = result.scalar()
                    
                    if table_exists:
                        conn.execute(text(f"GRANT SELECT ON TABLE {table_name} TO analytics_readonly"))
                        logger.info(f"Granted SELECT permissions")
                except Exception as grant_error:
                    logger.warning(f"Permission grant warning: {grant_error}")
            
            # Store metadata - FIXED: Cast to JSONB properly
            column_info = {
                "original": original_columns,
                "cleaned": cleaned_columns,
                "types": {k: str(v) for k, v in df.dtypes.items()}
            }
            
            # Convert to JSON string
            columns_json = json.dumps(column_info)
            
            with self.engine.connect() as conn:
                # Remove old entry if exists
                conn.execute(text("""
                    DELETE FROM data_sources WHERE table_name = :table_name
                """), {"table_name": table_name})
                
                # Insert new entry - FIXED: Proper parameter binding
                conn.execute(text("""
                    INSERT INTO data_sources 
                    (name, table_name, source_type, row_count, column_count, columns, description)
                    VALUES 
                    (:name, :table_name, :source_type, :row_count, :column_count, CAST(:columns AS jsonb), :description)
                """), {
                    "name": table_name.replace('_', ' ').title(),
                    "table_name": table_name,
                    "source_type": "csv_upload",
                    "row_count": int(len(df)),
                    "column_count": int(len(df.columns)),
                    "columns": columns_json,
                    "description": description or ""
                })
                conn.commit()
            
            logger.info(f"Successfully uploaded {len(df)} rows to {table_name}")
            
            return {
                "success": True,
                "table_name": table_name,
                "rows": len(df),
                "columns": cleaned_columns,
                "message": f"Successfully uploaded {len(df)} rows"
            }
            
        except Exception as e:
            logger.error(f"Error uploading CSV: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    def get_all_sources(self) -> List[Dict]:
        """Get all available data sources"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT name, table_name, source_type, row_count, column_count, 
                           uploaded_at, description
                    FROM data_sources
                    ORDER BY uploaded_at DESC
                """))
                
                sources = []
                for row in result:
                    sources.append({
                        "name": row[0],
                        "table_name": row[1],
                        "source_type": row[2],
                        "row_count": row[3],
                        "column_count": row[4],
                        "uploaded_at": row[5].isoformat() if row[5] else None,
                        "description": row[6]
                    })
                
                return sources
        except Exception as e:
            logger.error(f"Error getting sources: {e}")
            return []
    
    def get_table_info(self, table_name: str) -> Optional[Dict]:
        """Get detailed info about a table"""
        try:
            with self.engine.connect() as conn:
                # Get row count
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = result.scalar()
                
                # Get column info
                result = conn.execute(text(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = :table_name
                """), {"table_name": table_name})
                
                columns = [{"name": row[0], "type": row[1]} for row in result]
                
                # Get sample data
                result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 5"))
                sample = [dict(row._mapping) for row in result]
                
                return {
                    "table_name": table_name,
                    "row_count": row_count,
                    "columns": columns,
                    "sample_data": sample
                }
        except Exception as e:
            logger.error(f"Error getting table info: {e}")
            return None
    
    def delete_source(self, table_name: str) -> Dict:
        """Delete a data source"""
        try:
            with self.engine.connect() as conn:
                # Drop table
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                
                # Remove metadata
                conn.execute(text("""
                    DELETE FROM data_sources WHERE table_name = :table_name
                """), {"table_name": table_name})
                
                conn.commit()
            
            logger.info(f"Deleted data source: {table_name}")
            return {"success": True, "message": f"Deleted {table_name}"}
            
        except Exception as e:
            logger.error(f"Error deleting source: {e}")
            return {"success": False, "error": str(e)}