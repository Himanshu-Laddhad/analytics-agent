"""SQL safety validator using SQLGlot AST parsing"""
from .rules import SQLSafetyRules
import logging

logger = logging.getLogger(__name__)

def validate_sql_safety(state: dict) -> dict:
    """Validate SQL query for safety"""
    
    if state.get("sql_error") or state.get("error"):
        return state
    
    sql_query = state.get("sql_query")
    if not sql_query:
        return {
            **state,
            "sql_valid": False,
            "sql_error": "No SQL query to validate"
        }
    
    logger.info(f"Validating SQL safety: {sql_query[:100]}...")
    
    is_valid, errors = SQLSafetyRules.validate_query(sql_query)
    
    if is_valid:
        return {
            **state,
            "sql_valid": True,
            "sql_error": None
        }
    else:
        error_msg = "; ".join(errors)
        logger.error(f"SQL validation failed: {error_msg}")
        return {
            **state,
            "sql_valid": False,
            "sql_error": error_msg
        }