from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from .config import get_settings

# Setup logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Initialize telemetry BEFORE creating app
try:
    from .observability.tracer import setup_telemetry
    setup_telemetry()
except Exception as e:
    logger.warning(f"Telemetry setup skipped: {e}")

app = FastAPI(
    title="Analytics Agent API",
    version="1.0.0",
    debug=settings.DEBUG
)

# Instrument app with OpenTelemetry (if available)
try:
    from .observability.tracer import instrument_app
    instrument_app(app)
except Exception as e:
    logger.warning(f"Instrumentation skipped: {e}")

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

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Analytics Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """System health check"""
    health_status = {
        "status": "healthy",
        "database": "unknown",
        "redis": "unknown",
    }
    
    # Check database
    try:
        from .database import get_schema_info
        get_schema_info()
        health_status["database"] = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["database"] = "error"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        from .redis_client import cache
        if cache.health_check():
            health_status["redis"] = "ok"
        else:
            health_status["redis"] = "error"
            health_status["status"] = "degraded"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status["redis"] = "error"
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/schema")
async def get_database_schema():
    """Return database schema for reference"""
    try:
        from .database import get_schema_info
        schema = get_schema_info()
        return {"schema": schema}
    except Exception as e:
        logger.error(f"Schema fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Main endpoint - will integrate agents in Phase 2"""
    # Check cache first
    try:
        from .redis_client import cache
        if request.use_cache:
            cached_result = cache.get(request.query)
            if cached_result:
                cached_result["cached"] = True
                return cached_result
    except Exception as e:
        logger.warning(f"Cache check failed: {e}")
    
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