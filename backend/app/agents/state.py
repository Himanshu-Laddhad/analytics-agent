from typing import TypedDict, Optional, Any
import pandas as pd

class AgentState(TypedDict):
    """State shared across all agents in the graph"""
    
    # User input
    user_query: str
    use_cache: bool
    
    # Intent extraction
    intent: Optional[dict]  # {metrics, dimensions, filters, time_range}
    
    # SQL generation
    sql_query: Optional[str]
    sql_valid: bool
    sql_error: Optional[str]
    
    # Execution
    data: Optional[Any]  # Will be DataFrame or dict
    execution_error: Optional[str]
    
    # Interpretation
    data_profile: Optional[dict]  # {type, shape, columns, sample}
    
    # Visualization
    viz_plan: Optional[dict]  # {chart_type, x, y, color, title}
    viz_code: Optional[str]
    
    # Final output
    insight: Optional[str]
    error: Optional[str]