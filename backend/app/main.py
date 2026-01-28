from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from .config import get_settings
from .database import get_schema_info
from .redis_client import cache
from .observability.tracer import setup_telemetry, instrument_app
from .agents import agent_graph, AgentState
from fastapi import FastAPI, HTTPException, UploadFile, File
from .data_sources.manager import DataSourceManager
import pandas as pd
import io

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
        
        # Extract data from final state
        data_dict = final_state.get("data", {})
        data_profile = final_state.get("data_profile", {})
        
        # Build response with proper structure
        response = {
            "sql": final_state.get("sql_query") or "N/A",
            "visualization_code": final_state.get("viz_code") or "# No visualization generated",
            "insight": final_state.get("insight") or "Unable to generate insight",
            "data_summary": {
                "row_count": data_dict.get("row_count", 0),  # ← Fixed!
                "columns": data_dict.get("columns", []),      # ← Fixed!
                "type": data_profile.get("type", "unknown"),
                "data": data_dict.get("data", [])             # ← CRITICAL FIX!
            },
            "cached": False
        }
        
        # Debug logging
        logger.info(f"Response data_summary: row_count={response['data_summary']['row_count']}, "
                   f"columns={response['data_summary']['columns']}, "
                   f"data_len={len(response['data_summary']['data'])}")
        
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
    
# Initialize data source manager
data_source_manager = None

@app.on_event("startup")
async def startup_event():
    """Initialize data source manager on startup"""
    global data_source_manager
    data_source_manager = DataSourceManager(settings.DATABASE_URL)
    logger.info("Data source manager initialized")

@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...), table_name: str = None, description: str = ""):
    """Upload CSV file and create table"""
    try:
        # Read CSV
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Generate table name if not provided
        if not table_name:
            table_name = file.filename.replace('.csv', '').replace(' ', '_').lower()
        
        # Clean table name
        table_name = ''.join(c for c in table_name if c.isalnum() or c == '_')
        
        # Upload
        result = data_source_manager.upload_csv(df, table_name, description)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Upload failed"))
            
    except Exception as e:
        logger.error(f"CSV upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data-sources")
async def get_data_sources():
    """Get all available data sources"""
    try:
        sources = data_source_manager.get_all_sources()
        return {"sources": sources}
    except Exception as e:
        logger.error(f"Error getting data sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data-sources/{table_name}")
async def get_table_info(table_name: str):
    """Get detailed info about a table"""
    try:
        info = data_source_manager.get_table_info(table_name)
        if info:
            return info
        else:
            raise HTTPException(status_code=404, detail="Table not found")
    except Exception as e:
        logger.error(f"Error getting table info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/data-sources/{table_name}")
async def delete_data_source(table_name: str):
    """Delete a data source"""
    try:
        result = data_source_manager.delete_source(table_name)
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Delete failed"))
    except Exception as e:
        logger.error(f"Error deleting source: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        reload=settings.DEBUG
    )