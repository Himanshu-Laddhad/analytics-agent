from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
import os

# Get the backend directory
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str
    REDIS_TTL: int = 300
    
    # Groq
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    # OpenTelemetry
    OTEL_ENABLED: bool = True
    OTEL_SERVICE_NAME: str = "analytics-agent"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4318"
    
    # SQL Safety
    SQL_QUERY_TIMEOUT: int = 30
    SQL_MAX_ROWS: int = 10000
    SQL_MAX_JOINS: int = 3
    
    # API
    API_PORT: int = 8000
    DEBUG: bool = False
    
    class Config:
        # Look for .env in backend directory
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = 'utf-8'
        case_sensitive = False
        extra = 'ignore'

@lru_cache()
def get_settings() -> Settings:
    return Settings()