from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
import logging
import json
from ...config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Initialize Groq LLM
llm = ChatGroq(
    model=settings.GROQ_MODEL,
    api_key=settings.GROQ_API_KEY,
    temperature=0,
)

INTENT_SYSTEM_PROMPT = """You are an expert at understanding data analytics questions.

Extract these elements from the user's query:
- metrics: What are they measuring?
- dimensions: What are they grouping by?
- filters: Any conditions?
- aggregation: How to aggregate?
- time_range: Any time period?
- limit: How many results?

Database schema:
- customers: customer_id, customer_name, email, country, signup_date
- products: product_id, product_name, category, price, stock_quantity
- orders: order_id, customer_id, order_date, total_amount, status
- order_items: item_id, order_id, product_id, quantity, unit_price

Respond with JSON only:
{
  "metrics": ["total_amount"],
  "dimensions": ["product_name"],
  "filters": {},
  "aggregation": "sum",
  "limit": 5
}
"""

def extract_intent(state: dict) -> dict:
    """Extract user intent from natural language query"""
    logger.info(f"Extracting intent from: {state['user_query']}")
    
    try:
        messages = [
            SystemMessage(content=INTENT_SYSTEM_PROMPT),
            HumanMessage(content=f"Query: {state['user_query']}")
        ]
        
        response = llm.invoke(messages)
        
        # Parse JSON
        parser = JsonOutputParser()
        intent = parser.parse(response.content)
        
        logger.info(f"Extracted intent: {intent}")
        
        return {
            **state,
            "intent": intent,
            "error": None
        }
        
    except Exception as e:
        logger.error(f"Intent extraction error: {e}")
        return {
            **state,
            "intent": None,
            "error": f"Failed to understand query: {str(e)}"
        }