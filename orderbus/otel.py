"""
OpenTelemetry configuration for Django Orderbus.
"""
import logging
from opentelemetry import trace
# from opentelemetry import metrics  # Disabled - Jaeger doesn't support OTLP metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
# from opentelemetry.sdk.metrics import MeterProvider
# from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
# from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from django.conf import settings

logger = logging.getLogger(__name__)


def setup_otel():
    """Initialize OpenTelemetry instrumentation."""
    # Check if OTel is enabled
    otel_enabled = getattr(settings, "OTEL_ENABLED", False)
    if not otel_enabled:
        logger.info("OpenTelemetry is disabled. Skipping instrumentation.")
        return

    service_name = getattr(settings, "OTEL_SERVICE_NAME", "django-orderbus")
    jaeger_endpoint = getattr(
        settings, "OTEL_EXPORTER_JAEGER_ENDPOINT", "http://localhost:14268/api/traces"
    )
    otlp_endpoint = getattr(
        settings, "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces"
    )

    # Create resource with service name
    resource = Resource.create({"service.name": service_name})

    # Set up tracer provider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    # Configure exporter based on settings
    exporter_type = getattr(settings, "OTEL_EXPORTER_TYPE", "jaeger").lower()

    if exporter_type == "otlp":
        # Use OTLP exporter (recommended for production)
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        logger.info(f"Using OTLP exporter with endpoint: {otlp_endpoint}")
    else:
        # Use Jaeger exporter (simpler for local development)
        # For local Docker setup, use collector_endpoint (HTTP)
        exporter = JaegerExporter(
            collector_endpoint=jaeger_endpoint,
        )
        logger.info(f"Using Jaeger exporter with collector endpoint: {jaeger_endpoint}")

    # Add span processor
    span_processor = BatchSpanProcessor(exporter)
    tracer_provider.add_span_processor(span_processor)

    # Instrument Django
    DjangoInstrumentor().instrument()

    # Instrument PostgreSQL
    Psycopg2Instrumentor().instrument()

    # Set up metrics provider if enabled
    # Note: Jaeger all-in-one doesn't support OTLP metrics endpoint (/v1/metrics)
    # We use django-prometheus for application metrics instead
    metrics_enabled = getattr(settings, "OTEL_EXPORTER_METRICS_ENABLED", False)
    if metrics_enabled:
        logger.warning(
            "OTel metrics export is enabled but Jaeger doesn't support OTLP metrics. "
            "Use django-prometheus for metrics instead. Disabling OTel metrics export."
        )
        # Uncomment below if you have an OTLP collector that supports metrics
        # otlp_metrics_endpoint = otlp_endpoint.replace("/v1/traces", "/v1/metrics")
        # metric_exporter = OTLPMetricExporter(endpoint=otlp_metrics_endpoint)
        # metric_reader = PeriodicExportingMetricReader(
        #     exporter=metric_exporter,
        #     export_interval_millis=15000,
        # )
        # meter_provider = MeterProvider(
        #     metric_readers=[metric_reader],
        #     resource=resource,
        # )
        # metrics.set_meter_provider(meter_provider)

    logger.info(f"OpenTelemetry instrumentation enabled for service: {service_name}")


