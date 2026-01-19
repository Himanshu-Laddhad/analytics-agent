from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str
    REDIS_TTL: int = 300  # 5 minutes
    
    # Groq (replacing OpenAI)
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"  # Fast and smart
    # Alternative models:
    # "llama-3.1-70b-versatile" - Very capable
    # "mixtral-8x7b-32768" - Good for long context
    # "gemma2-9b-it" - Faster, lighter
    
    # OpenTelemetry
    OTEL_ENABLED: bool = True
    OTEL_SERVICE_NAME: str = "analytics-agent"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://jaeger:4318"
    
    # SQL Safety
    SQL_QUERY_TIMEOUT: int = 30  # seconds
    SQL_MAX_ROWS: int = 10000
    SQL_MAX_JOINS: int = 3
    
    # API
    API_PORT: int = 8000
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()