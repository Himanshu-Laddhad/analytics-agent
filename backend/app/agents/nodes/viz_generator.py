import logging

logger = logging.getLogger(__name__)

def generate_viz_code(state: dict) -> dict:
    """Generate Plotly visualization code based on plan"""
    
    viz_plan = state.get("viz_plan", {})
    
    if not viz_plan:
        logger.info("No visualization plan available")
        return {
            **state,
            "viz_code": "# No visualization generated"
        }
    
    chart_type = viz_plan.get("chart_type", "bar")
    x_axis = viz_plan.get("x_axis", "")
    y_axis = viz_plan.get("y_axis", "")
    title = viz_plan.get("title", "Data Visualization")
    
    logger.info(f"Generating {chart_type} visualization code")
    
    # Generate appropriate chart code
    if chart_type == "line":
        viz_code = f"""import plotly.graph_objects as go

fig = go.Figure(data=[
    go.Scatter(
        x=df['{x_axis}'],
        y=df['{y_axis}'],
        mode='lines+markers',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8, color='#1f77b4')
    )
])

fig.update_layout(
    title=dict(
        text='{title}',
        font=dict(size=20, color='#262730'),
        x=0.5,
        xanchor='center'
    ),
    xaxis=dict(
        title='{x_axis.replace("_", " ").title()}',
        showgrid=True,
        gridcolor='#e0e0e0',
        title_font=dict(size=14, color='#262730')
    ),
    yaxis=dict(
        title='{y_axis.replace("_", " ").title()}',
        showgrid=True,
        gridcolor='#e0e0e0',
        rangemode='tozero',
        title_font=dict(size=14, color='#262730')
    ),
    plot_bgcolor='white',
    paper_bgcolor='white',
    hovermode='x unified',
    height=500
)
"""
    
    elif chart_type == "bar":
        viz_code = f"""import plotly.graph_objects as go

fig = go.Figure(data=[
    go.Bar(
        x=df['{x_axis}'],
        y=df['{y_axis}'],
        marker=dict(
            color='#1f77b4',
            line=dict(color='#0d47a1', width=1.5)
        ),
        text=df['{y_axis}'].round(2),
        textposition='outside',
        textfont=dict(size=12)
    )
])

fig.update_layout(
    title=dict(
        text='{title}',
        font=dict(size=20, color='#262730'),
        x=0.5,
        xanchor='center'
    ),
    xaxis=dict(
        title='{x_axis.replace("_", " ").title()}',
        showgrid=False,
        title_font=dict(size=14, color='#262730'),
        tickfont=dict(size=11)
    ),
    yaxis=dict(
        title='{y_axis.replace("_", " ").title()}',
        showgrid=True,
        gridcolor='#e0e0e0',
        rangemode='tozero',
        title_font=dict(size=14, color='#262730'),
        tickfont=dict(size=11)
    ),
    plot_bgcolor='white',
    paper_bgcolor='white',
    hovermode='x',
    height=500,
    bargap=0.2
)

# Format y-axis based on data type
if df['{y_axis}'].dtype in ['float64', 'float32', 'int64', 'int32']:
    # Check if values are likely currency
    max_val = df['{y_axis}'].max()
    if max_val > 100:
        fig.update_yaxes(tickprefix='$', tickformat=',.2f')
"""
    
    else:
        # Default to bar chart
        viz_code = f"""import plotly.graph_objects as go

fig = go.Figure(data=[
    go.Bar(
        x=df['{x_axis}'],
        y=df['{y_axis}'],
        marker=dict(color='#1f77b4')
    )
])

fig.update_layout(
    title='{title}',
    xaxis_title='{x_axis.replace("_", " ").title()}',
    yaxis_title='{y_axis.replace("_", " ").title()}',
    yaxis=dict(rangemode='tozero'),
    template='plotly_white',
    height=500
)
"""
    
    logger.info("Generated visualization code")
    
    return {
        **state,
        "viz_code": viz_code
    }