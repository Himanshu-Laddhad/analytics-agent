from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from .config import get_settings
from .database import get_schema_info
from .redis_client import cache
from .observability.tracer import setup_telemetry, instrument_app
from agents import agent_graph, AgentState

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Initialize telemetry BEFORE creating app
setup_telemetry()

app = FastAPI(
    title="Analytics Agent API",
    version="1.0.0",
    debug=settings.DEBUG
)

# Instrument app with OpenTelemetry
instrument_app(app)

# CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class QueryRequest(BaseModel):
    query: str
    use_cache: bool = True

class QueryResponse(BaseModel):
    sql: str
    visualization_code: str
    insight: str
    data_summary: dict
    cached: bool = False

@app.get("/health")
async def health_check():
    """System health check"""
    db_healthy = True
    redis_healthy = cache.health_check()
    
    try:
        get_schema_info()
    except:
        db_healthy = False
    
    return {
        "status": "healthy" if (db_healthy and redis_healthy) else "degraded",
        "database": "ok" if db_healthy else "error",
        "redis": "ok" if redis_healthy else "error",
    }

@app.get("/schema")
async def get_database_schema():
    """Return database schema for reference"""
    try:
        schema = get_schema_info()
        return {"schema": schema}
    except Exception as e:
        logger.error(f"Schema fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Main endpoint - processes natural language query through agent graph"""
    
    logger.info(f"Processing query: {request.query}")
    
    # Check cache first
    if request.use_cache:
        cached_result = cache.get(request.query)
        if cached_result:
            logger.info("Returning cached result")
            cached_result["cached"] = True
            return cached_result
    
    try:
        # Initialize agent state
        initial_state: AgentState = {
            "user_query": request.query,
            "use_cache": request.use_cache,
            "intent": None,
            "sql_query": None,
            "sql_valid": False,
            "sql_error": None,
            "data": None,
            "execution_error": None,
            "data_profile": None,
            "viz_plan": None,
            "viz_code": None,
            "insight": None,
            "error": None
        }
        
        # Run through agent graph
        logger.info("Starting agent graph execution")
        final_state = agent_graph.invoke(initial_state)
        
        # Build response
        response = {
            "sql": final_state.get("sql_query") or "N/A",
            "visualization_code": final_state.get("viz_code") or "# No visualization generated",
            "insight": final_state.get("insight") or "Unable to generate insight",
            "data_summary": {
                "rows": final_state.get("data_profile", {}).get("row_count", 0),
                "columns": final_state.get("data_profile", {}).get("columns", []),
                "type": final_state.get("data_profile", {}).get("type", "unknown")
            },
            "cached": False
        }
        
        # Cache successful results
        if request.use_cache and not final_state.get("error"):
            cache.set(request.query, response)
        
        logger.info("Query processed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Query processing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process query: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        reload=settings.DEBUG
    )