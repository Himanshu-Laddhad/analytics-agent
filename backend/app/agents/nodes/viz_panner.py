from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
import logging
import json
from ...config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

llm = ChatGroq(
    model=settings.GROQ_MODEL,
    api_key=settings.GROQ_API_KEY,
    temperature=0,
)

VIZ_PLANNER_PROMPT = """You are a data visualization expert.

Your job is to decide the BEST chart type for the given data and query.

Available chart types:
- bar: For categorical comparisons (top products, sales by category)
- line: For time series trends (daily revenue, monthly growth)
- scatter: For correlations (price vs quantity)
- pie: For part-to-whole (market share, category distribution) - use sparingly
- table: For detailed data listing

Consider:
- Data type (time_series, categorical, ranking, tabular)
- Number of data points
- User's question intent
- Best practices for clarity

Respond ONLY with valid JSON:
{
  "chart_type": "bar",
  "x_axis": "product_name",
  "y_axis": "total_revenue",
  "title": "Top Products by Revenue",
  "x_label": "Product",
  "y_label": "Revenue ($)",
  "color": null,
  "sort_by": "y_axis",
  "sort_order": "desc"
}

For time series, use "line" and ensure x_axis is the date column.
For rankings, use "bar" with sort_order "desc".
"""

def plan_visualization(state: dict) -> dict:
    """Plan the best visualization for the data"""
    
    if state.get("error") or state.get("execution_error"):
        return state
    
    data_profile = state.get("data_profile")
    if not data_profile or data_profile.get("type") == "empty":
        return {
            **state,
            "viz_plan": None
        }
    
    logger.info(f"Planning visualization for {data_profile.get('type')} data")
    
    try:
        # Build context for LLM
        context = f"""
User Query: {state['user_query']}

Data Profile:
- Type: {data_profile.get('type')}
- Rows: {data_profile.get('row_count')}
- Columns: {', '.join(data_profile.get('columns', []))}

Sample Data:
{json.dumps(data_profile.get('sample', []), indent=2)}

Intent:
{json.dumps(state.get('intent', {}), indent=2)}
"""
        
        messages = [
            SystemMessage(content=VIZ_PLANNER_PROMPT),
            HumanMessage(content=context)
        ]
        
        response = llm.invoke(messages)
        
        # Parse JSON response
        parser = JsonOutputParser()
        viz_plan = parser.parse(response.content)
        
        logger.info(f"Visualization plan: {viz_plan['chart_type']}")
        
        return {
            **state,
            "viz_plan": viz_plan
        }
        
    except Exception as e:
        logger.error(f"Visualization planning error: {e}")
        # Fallback to simple bar chart
        columns = data_profile.get('columns', [])
        return {
            **state,
            "viz_plan": {
                "chart_type": "bar",
                "x_axis": columns[0] if len(columns) > 0 else "x",
                "y_axis": columns[1] if len(columns) > 1 else "y",
                "title": "Query Results",
                "x_label": "Category",
                "y_label": "Value"
            }
        }