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
    temperature=0.3,  # Slightly creative for insights
)

INSIGHT_PROMPT = """You are a data analyst providing insights from query results.

Generate a concise, actionable insight (2-3 sentences) that:
1. Answers the user's original question
2. Highlights key findings from the data
3. Provides context or recommendations when relevant

Be specific with numbers and trends.
Be conversational but professional.
Focus on what matters most to the user.
"""

def generate_insight(state: dict) -> dict:
    """Generate natural language insight from results"""
    
    if state.get("error") or state.get("execution_error"):
        return state
    
    data_profile = state.get("data_profile")
    if not data_profile or data_profile.get("type") == "empty":
        return {
            **state,
            "insight": "No data found matching your query."
        }
    
    logger.info("Generating insight from results")
    
    try:
        context = f"""
User Question: {state['user_query']}

Data Summary:
- {data_profile.get('row_count')} results
- Type: {data_profile.get('type')}

Top Results:
{json.dumps(data_profile.get('sample', []), indent=2)}

SQL Query Used:
{state.get('sql_query')}
"""
        
        messages = [
            SystemMessage(content=INSIGHT_PROMPT),
            HumanMessage(content=context)
        ]
        
        response = llm.invoke(messages)
        insight = response.content.strip()
        
        logger.info(f"Generated insight: {insight[:100]}...")
        
        return {
            **state,
            "insight": insight
        }
        
    except Exception as e:
        logger.error(f"Insight generation error: {e}")
        return {
            **state,
            "insight": f"Found {data_profile.get('row_count', 0)} results for your query."
        }