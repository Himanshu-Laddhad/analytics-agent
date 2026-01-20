from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
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

VIZ_CODE_PROMPT = """You are a Plotly expert code generator.

Generate COMPLETE, EXECUTABLE Python code using Plotly that creates an interactive visualization.

CRITICAL REQUIREMENTS:
1. Use plotly.graph_objects (import plotly.graph_objects as go)
2. Code must be COMPLETE and RUNNABLE
3. Data is already available as a pandas DataFrame called 'df'
4. Return ONLY the code, no explanations or markdown
5. Create a variable called 'fig' with the final figure
6. Include proper titles, labels, and formatting
7. Use .update_layout() for styling
8. Make it interactive (hover tooltips, etc.)

Example structure:
```python
import plotly.graph_objects as go

fig = go.Figure(data=[
    go.Bar(x=df['column1'], y=df['column2'], name='Series Name')
])

fig.update_layout(
    title='Chart Title',
    xaxis_title='X Label',
    yaxis_title='Y Label',
    hovermode='x unified',
    template='plotly_white'
)
```

Generate code that follows this pattern but matches the requested chart type and data.
"""

def generate_visualization_code(state: dict) -> dict:
    """Generate Plotly code for visualization"""
    
    if state.get("error") or state.get("execution_error"):
        return state
    
    viz_plan = state.get("viz_plan")
    data_profile = state.get("data_profile")
    
    if not viz_plan or not data_profile:
        return {
            **state,
            "viz_code": None
        }
    
    logger.info(f"Generating {viz_plan['chart_type']} visualization code")
    
    try:
        # Build prompt with plan and data context
        context = f"""
Visualization Plan:
{json.dumps(viz_plan, indent=2)}

Data Profile:
- Columns: {', '.join(data_profile.get('columns', []))}
- Row Count: {data_profile.get('row_count')}
- Sample: {json.dumps(data_profile.get('sample', [])[:2], indent=2)}

Generate complete Plotly code for a {viz_plan['chart_type']} chart.
Remember: DataFrame 'df' is already available with this data.
"""
        
        messages = [
            SystemMessage(content=VIZ_CODE_PROMPT),
            HumanMessage(content=context)
        ]
        
        response = llm.invoke(messages)
        viz_code = response.content.strip()
        
        # Remove markdown code blocks if present
        if viz_code.startswith("```"):
            viz_code = viz_code.split("```")[1]
            if viz_code.startswith("python"):
                viz_code = viz_code[6:]
            viz_code = viz_code.strip()
            if viz_code.endswith("```"):
                viz_code = viz_code[:-3].strip()
        
        logger.info(f"Generated visualization code ({len(viz_code)} chars)")
        
        return {
            **state,
            "viz_code": viz_code
        }
        
    except Exception as e:
        logger.error(f"Visualization code generation error: {e}")
        # Fallback to simple code
        x_col = viz_plan.get('x_axis', 'x')
        y_col = viz_plan.get('y_axis', 'y')
        
        fallback_code = f"""import plotly.graph_objects as go

fig = go.Figure(data=[
    go.Bar(x=df['{x_col}'], y=df['{y_col}'])
])

fig.update_layout(
    title='{viz_plan.get("title", "Results")}',
    xaxis_title='{viz_plan.get("x_label", "X")}',
    yaxis_title='{viz_plan.get("y_label", "Y")}',
    template='plotly_white'
)
"""
        
        return {
            **state,
            "viz_code": fallback_code
        }