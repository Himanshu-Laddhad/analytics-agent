from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
import logging
from ..config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

def setup_telemetry():
    """Initialize OpenTelemetry tracing"""
    if not settings.OTEL_ENABLED:
        logger.info("OpenTelemetry disabled")
        return
    
    # Define service resource
    resource = Resource.create({
        "service.name": settings.OTEL_SERVICE_NAME,
        "service.version": "1.0.0",
    })
    
    # Set up tracer provider
    provider = TracerProvider(resource=resource)
    
    # Configure OTLP exporter (sends to Jaeger, Honeycomb, etc.)
    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
    )
    
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(provider)
    
    logger.info(f"OpenTelemetry initialized: {settings.OTEL_SERVICE_NAME}")

def instrument_app(app):
    """Auto-instrument FastAPI and dependencies"""
    if not settings.OTEL_ENABLED:
        return
    
    # Instrument FastAPI (automatic endpoint tracing)
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument SQLAlchemy (database query tracing)
    from ..database import engine
    SQLAlchemyInstrumentor().instrument(engine=engine)
    
    # Instrument Redis (cache operation tracing)
    RedisInstrumentor().instrument()
    
    logger.info("Auto-instrumentation complete")

# Get tracer for manual spans
tracer = trace.get_tracer(__name__)