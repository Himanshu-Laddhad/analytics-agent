from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from .config import get_settings
from .database import get_schema_info
from .redis_client import cache
from .observability.tracer import setup_telemetry, instrument_app

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
    """Main endpoint - will integrate agents in Phase 2"""
    # Check cache first
    if request.use_cache:
        cached_result = cache.get(request.query)
        if cached_result:
            cached_result["cached"] = True
            return cached_result
    
    # Placeholder - we'll add agent graph here
    return {
        "sql": "SELECT * FROM orders LIMIT 10",
        "visualization_code": "# Plotly code here",
        "insight": "System initialized - agents coming in Phase 2",
        "data_summary": {"rows": 0},
        "cached": False
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        reload=settings.DEBUG
    )