import logging
import json

logger = logging.getLogger(__name__)

def generate_insight(state: dict) -> dict:
    """Generate insight from results"""
    
    if state.get("error") or state.get("execution_error"):
        return state
    
    data_profile = state.get("data_profile")
    if not data_profile or data_profile.get("type") == "empty":
        return {
            **state,
            "insight": "No data found."
        }
    
    logger.info("Generating insight")
    
    try:
        row_count = data_profile.get("row_count", 0)
        sample = data_profile.get("sample", [])
        
        if sample:
            top_item = sample[0]
            keys = list(top_item.keys())
            insight = f"Found {row_count} results. "
            if len(keys) >= 2:
                insight += f"Top result: {top_item.get(keys[0])} with {top_item.get(keys[1])}."
        else:
            insight = f"Query returned {row_count} results."
        
        logger.info(f"Generated insight: {insight}")
        
        return {
            **state,
            "insight": insight
        }
        
    except Exception as e:
        logger.error(f"Insight error: {e}")
        return {
            **state,
            "insight": "Results found."
        }