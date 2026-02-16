from __future__ import annotations

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

from azure.monitor.opentelemetry import configure_azure_monitor

from insurance_agent.config import Settings


def initialize_telemetry(settings: Settings) -> None:
    if not settings.app_insights_connection_string:
        return
    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "service.version": settings.otel_service_version,
        }
    )
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    configure_azure_monitor(
        connection_string=settings.app_insights_connection_string,
        tracer_provider=tracer_provider,
    )
