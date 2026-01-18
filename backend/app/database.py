from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import logging
from .config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Create engine with read-only user (CRITICAL for safety)
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before use
    echo=settings.DEBUG,
)

# Add query timeout listener (safety layer)
@event.listens_for(engine, "connect")
def set_timeout(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute(f"SET statement_timeout = {settings.SQL_QUERY_TIMEOUT * 1000}")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

@contextmanager
def get_db():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def get_schema_info() -> dict:
    """Extract database schema for LLM context"""
    with get_db() as db:
        # Get tables (excluding system tables)
        tables_query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """)
        tables = [row[0] for row in db.execute(tables_query)]
        
        schema = {}
        for table in tables:
            # Get columns for each table
            columns_query = text(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = :table_name
                ORDER BY ordinal_position
            """)
            columns = db.execute(columns_query, {"table_name": table}).fetchall()
            schema[table] = [
                {"name": col[0], "type": col[1]} for col in columns
            ]
    
    return schema