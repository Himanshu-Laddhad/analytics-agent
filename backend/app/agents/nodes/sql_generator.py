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

SQL_SYSTEM_PROMPT = """You are an expert SQL generator for PostgreSQL.

RULES:
1. SELECT queries only
2. ALWAYS include LIMIT (max 10000)
3. Use proper JOINs
4. Use aggregate functions when needed
5. Use GROUP BY with aggregates
6. Use ORDER BY for sorting

Database schema:
- customers: customer_id, customer_name, email, country, signup_date
- products: product_id, product_name, category, price, stock_quantity
- orders: order_id, customer_id, order_date, total_amount, status
- order_items: item_id, order_id, product_id, quantity, unit_price

Generate ONLY the SQL query, no explanation.
"""

def generate_sql(state: dict) -> dict:
    """Generate SQL query from intent"""
    
    if state.get("error"):
        return state
    
    intent = state.get("intent")
    if not intent:
        return {
            **state,
            "sql_query": None,
            "error": "No intent available"
        }
    
    logger.info(f"Generating SQL for intent: {intent}")
    
    try:
        intent_str = json.dumps(intent, indent=2)
        prompt = f"""Generate SQL for this intent:

{intent_str}

Original question: {state['user_query']}
"""
        
        messages = [
            SystemMessage(content=SQL_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        sql_query = response.content.strip()
        
        # Remove markdown
        if sql_query.startswith("```"):
            sql_query = sql_query.split("```")[1]
            if sql_query.startswith("sql"):
                sql_query = sql_query[3:]
            sql_query = sql_query.strip()
        
        logger.info(f"Generated SQL: {sql_query}")
        
        return {
            **state,
            "sql_query": sql_query,
            "sql_valid": False,
            "sql_error": None
        }
        
    except Exception as e:
        logger.error(f"SQL generation error: {e}")
        return {
            **state,
            "sql_query": None,
            "sql_error": f"Failed to generate SQL: {str(e)}"
        }