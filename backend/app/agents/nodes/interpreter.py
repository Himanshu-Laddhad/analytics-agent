import pandas as pd
import logging

logger = logging.getLogger(__name__)

def interpret_data(state: dict) -> dict:
    """Analyze data shape and type"""
    
    if state.get("error") or state.get("execution_error"):
        return state
    
    data_dict = state.get("data")
    if not data_dict:
        return {
            **state,
            "data_profile": None
        }
    
    logger.info("Interpreting data")
    
    try:
        df = pd.DataFrame(data_dict["data"])
        
        if df.empty:
            return {
                **state,
                "data_profile": {
                    "type": "empty",
                    "message": "No results"
                }
            }
        
        profile = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": df.columns.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
        
        # Detect type
        date_cols = [col for col in df.columns if 'date' in col.lower()]
        if date_cols:
            profile["type"] = "time_series"
            profile["time_column"] = date_cols[0]
        elif len(df.columns) == 2:
            profile["type"] = "categorical"
        else:
            profile["type"] = "tabular"
        
        profile["sample"] = df.head(3).to_dict(orient="records")
        
        logger.info(f"Data profile: {profile['type']}")
        
        return {
            **state,
            "data_profile": profile
        }
        
    except Exception as e:
        logger.error(f"Interpretation error: {e}")
        return {
            **state,
            "data_profile": {"type": "error", "message": str(e)}
        }