import pandas as pd
import logging

logger = logging.getLogger(__name__)

def interpret_data(state: dict) -> dict:
    """Analyze and profile the returned data"""
    
    if state.get("error") or state.get("execution_error"):
        return state
    
    data_dict = state.get("data")
    if not data_dict:
        return {
            **state,
            "data_profile": None
        }
    
    logger.info("Interpreting data shape and type")
    
    try:
        # Reconstruct DataFrame
        df = pd.DataFrame(data_dict["data"])
        
        if df.empty:
            return {
                **state,
                "data_profile": {
                    "type": "empty",
                    "message": "Query returned no results"
                }
            }
        
        # Detect data type
        profile = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": df.columns.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
        
        # Detect time series
        date_columns = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
        if date_columns:
            profile["type"] = "time_series"
            profile["time_column"] = date_columns[0]
        
        # Detect categorical aggregation
        elif len(df.columns) == 2:
            profile["type"] = "categorical"
            profile["category_column"] = df.columns[0]
            profile["value_column"] = df.columns[1]
        
        # Detect top-N ranking
        elif any("total" in col.lower() or "sum" in col.lower() or "count" in col.lower() for col in df.columns):
            profile["type"] = "ranking"
        
        else:
            profile["type"] = "tabular"
        
        # Add sample data
        profile["sample"] = df.head(3).to_dict(orient="records")
        
        logger.info(f"Data profile: {profile['type']}, {profile['row_count']} rows")
        
        return {
            **state,
            "data_profile": profile
        }
        
    except Exception as e:
        logger.error(f"Data interpretation error: {e}")
        return {
            **state,
            "data_profile": {"type": "error", "message": str(e)}
        }