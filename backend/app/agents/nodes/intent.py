from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
import logging
from ...config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Initialize Groq LLM
llm = ChatGroq(
    model=settings.GROQ_MODEL,
    api_key=settings.GROQ_API_KEY,
    temperature=0,  # Deterministic for analytics
)

INTENT_SYSTEM_PROMPT = """You are an expert at understanding data analytics questions.

Your job is to extract the user's intent from their natural language query.

Extract these elements:
- metrics: What are they measuring? (revenue, count, average, etc.)
- dimensions: What are they grouping by? (product, date, customer, etc.)
- filters: Any conditions? (date ranges, categories, status, etc.)
- aggregation: How to aggregate? (sum, count, avg, max, min)
- time_range: Any time period mentioned? (last month, this year, etc.)
- limit: How many results? (top 5, first 10, etc.)

Database schema context:
- customers: customer_id, customer_name, email, country, signup_date
- products: product_id, product_name, category, price, stock_quantity
- orders: order_id, customer_id, order_date, total_amount, status
- order_items: item_id, order_id, product_id, quantity, unit_price

Respond ONLY with valid JSON in this format:
{
  "metrics": ["total_amount", "quantity"],
  "dimensions": ["product_name"],
  "filters": {"order_date": ">= '2025-01-01'"},
  "aggregation": "sum",
  "time_range": "this_month",
  "limit": 5,
  "sort": "desc"
}

If unclear, make reasonable assumptions based on common analytics patterns.
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
        
        # Parse JSON response
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