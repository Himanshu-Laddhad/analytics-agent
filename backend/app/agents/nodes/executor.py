import pandas as pd
from sqlalchemy import text
import logging
from ...database import get_db

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
            
            logger.info(f"Query executed: {len(data)} rows")
            
            # Convert DataFrame to dict for JSON serialization
            # CRITICAL: Include the actual data!
            data_dict = {
                "columns": columns,
                "data": data.to_dict(orient="records"),  # ← This is the key fix!
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
        logger.error(f"Execution error: {e}")
        return {
            **state,
            "data": None,
            "execution_error": f"Database error: {str(e)}"
        }