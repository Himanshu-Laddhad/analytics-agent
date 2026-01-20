import logging

logger = logging.getLogger(__name__)

def generate_visualization_code(state: dict) -> dict:
    """Generate Plotly code"""
    
    if state.get("error") or state.get("execution_error"):
        return state
    
    viz_plan = state.get("viz_plan")
    if not viz_plan:
        return {
            **state,
            "viz_code": None
        }
    
    logger.info(f"Generating {viz_plan['chart_type']} code")
    
    try:
        chart_type = viz_plan['chart_type']
        x_axis = viz_plan.get('x_axis', 'x')
        y_axis = viz_plan.get('y_axis', 'y')
        title = viz_plan.get('title', 'Results')
        
        if chart_type == "line":
            trace = f"go.Scatter(x=df['{x_axis}'], y=df['{y_axis}'], mode='lines+markers')"
        else:  # bar
            trace = f"go.Bar(x=df['{x_axis}'], y=df['{y_axis}'])"
        
        viz_code = f"""import plotly.graph_objects as go

fig = go.Figure(data=[
    {trace}
])

fig.update_layout(
    title='{title}',
    xaxis_title='{x_axis}',
    yaxis_title='{y_axis}',
    template='plotly_white'
)
"""
        
        logger.info("Generated viz code")
        
        return {
            **state,
            "viz_code": viz_code
        }
        
    except Exception as e:
        logger.error(f"Viz generation error: {e}")
        return {
            **state,
            "viz_code": "# Error generating visualization"
        }