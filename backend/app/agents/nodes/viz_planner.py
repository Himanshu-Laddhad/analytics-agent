import logging
import json

logger = logging.getLogger(__name__)

def plan_visualization(state: dict) -> dict:
    """Plan visualization based on data type"""
    
    if state.get("error") or state.get("execution_error"):
        return state
    
    data_profile = state.get("data_profile")
    if not data_profile or data_profile.get("type") == "empty":
        return {
            **state,
            "viz_plan": None
        }
    
    logger.info(f"Planning viz for {data_profile.get('type')} data")
    
    try:
        columns = data_profile.get("columns", [])
        data_type = data_profile.get("type")
        
        # Simple rule-based planning
        if data_type == "time_series":
            viz_plan = {
                "chart_type": "line",
                "x_axis": data_profile.get("time_column", columns[0]),
                "y_axis": columns[1] if len(columns) > 1 else columns[0],
                "title": "Trend Over Time"
            }
        elif data_type == "categorical":
            viz_plan = {
                "chart_type": "bar",
                "x_axis": columns[0],
                "y_axis": columns[1],
                "title": "Comparison"
            }
        else:
            viz_plan = {
                "chart_type": "bar",
                "x_axis": columns[0] if columns else "x",
                "y_axis": columns[1] if len(columns) > 1 else "y",
                "title": "Results"
            }
        
        logger.info(f"Viz plan: {viz_plan['chart_type']}")
        
        return {
            **state,
            "viz_plan": viz_plan
        }
        
    except Exception as e:
        logger.error(f"Viz planning error: {e}")
        return {
            **state,
            "viz_plan": {"chart_type": "bar", "x_axis": "x", "y_axis": "y", "title": "Results"}
        }