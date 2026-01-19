from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
import logging

logger = logging.getLogger(__name__)

def setup_telemetry():
    """Initialize OpenTelemetry tracing"""
    from ..config import get_settings
    settings = get_settings()
    
    if not settings.OTEL_ENABLED:
        logger.info("OpenTelemetry disabled")
        return
    
    try:
        # Define service resource
        resource = Resource.create({
            "service.name": settings.OTEL_SERVICE_NAME,
            "service.version": "1.0.0",
        })
        
        # Set up tracer provider
        provider = TracerProvider(resource=resource)
        
        # Configure OTLP exporter
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        )
        
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        trace.set_tracer_provider(provider)
        
        logger.info(f"OpenTelemetry initialized: {settings.OTEL_SERVICE_NAME}")
    except Exception as e:
        logger.warning(f"Failed to initialize OpenTelemetry: {e}")

def instrument_app(app):
    """Auto-instrument FastAPI and dependencies"""
    from ..config import get_settings
    settings = get_settings()
    
    if not settings.OTEL_ENABLED:
        return
    
    try:
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        
        # Instrument SQLAlchemy
        from ..database import engine
        SQLAlchemyInstrumentor().instrument(engine=engine)
        
        # Instrument Redis
        RedisInstrumentor().instrument()
        
        logger.info("Auto-instrumentation complete")
    except Exception as e:
        logger.warning(f"Failed to instrument app: {e}")

# Get tracer for manual spans
tracer = trace.get_tracer(__name__)