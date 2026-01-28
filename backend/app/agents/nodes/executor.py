import pandas as pd
from sqlalchemy import text
import logging
from ...database import get_db
import decimal
import datetime

logger = logging.getLogger(__name__)

def execute_query(state: dict) -> dict:
    """Execute validated SQL query"""
    
    if state.get("error") or state.get("sql_error"):
        return state
    
    if not state.get("sql_valid"):
        return {
            **state,
            "execution_error": "Cannot execute invalid SQL"
        }
    
    sql_query = state.get("sql_query")
    if not sql_query:
        return {
            **state,
            "execution_error": "No SQL query to execute"
        }
    
    logger.info(f"Executing query: {sql_query}")
    
    try:
        with get_db() as db:
            result = db.execute(text(sql_query))
            
            # Fetch all rows
            rows = result.fetchall()
            columns = list(result.keys())
            
            # Convert to pandas DataFrame
            data = pd.DataFrame(rows, columns=columns)
            
            # CRITICAL: Convert decimal and datetime objects to JSON-serializable types
            for col in data.columns:
                if data[col].dtype == 'object':
                    # Check if it's numeric but stored as object
                    try:
                        data[col] = pd.to_numeric(data[col])
                    except:
                        pass
                    
                    # Convert decimals to float
                    if any(isinstance(x, decimal.Decimal) for x in data[col] if x is not None):
                        data[col] = data[col].apply(lambda x: float(x) if isinstance(x, decimal.Decimal) else x)
                    
                    # Convert dates to string
                    if any(isinstance(x, (datetime.date, datetime.datetime)) for x in data[col] if x is not None):
                        data[col] = data[col].apply(lambda x: x.isoformat() if isinstance(x, (datetime.date, datetime.datetime)) else x)
            
            logger.info(f"Query executed: {len(data)} rows")
            logger.info(f"Column types: {data.dtypes.to_dict()}")
            
            # Convert DataFrame to dict for JSON serialization
            data_dict = {
                "columns": columns,
                "data": data.to_dict(orient="records"),
                "row_count": len(data)
            }
            
            # Debug log
            logger.info(f"Returning data with {len(data)} rows, columns: {columns}")
            
            return {
                **state,
                "data": data_dict,
                "execution_error": None
            }
            
    except Exception as e:
        logger.error(f"Execution error: {e}", exc_info=True)
        return {
            **state,
            "data": None,
            "execution_error": f"Database error: {str(e)}"
        }