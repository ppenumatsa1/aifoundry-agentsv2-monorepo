from __future__ import annotations

from dataclasses import dataclass
import logging
import os

from azure.ai.projects.telemetry import AIProjectInstrumentor
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.trace import Span

from sharepoint_agent.config import Settings


@dataclass(frozen=True)
class TelemetryConfig:
    connection_string: str
    service_name: str
    service_version: str
    environment: str
    capture_message_content: bool


class TraceContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        span = trace.get_current_span()
        context = span.get_span_context() if span else None
        if context and context.is_valid:
            record.trace_id = format(context.trace_id, "032x")
            record.span_id = format(context.span_id, "016x")
        else:
            record.trace_id = ""
            record.span_id = ""
        return True


class AgentDimensionSpanProcessor(SpanProcessor):
    def __init__(self, agent_name: str | None) -> None:
        self._agent_name = agent_name

    def on_start(self, span: Span, parent_context: object | None = None) -> None:
        if not span.is_recording():
            return
        span.set_attribute("gen_ai.system", "az.ai.agents")
        if self._agent_name and "gen_ai.agent.name" not in span.attributes:
            span.set_attribute("gen_ai.agent.name", self._agent_name)

    def on_end(self, span: object) -> None:
        return None

    def shutdown(self) -> None:
        return None

    def force_flush(self, timeout_millis: int | None = None) -> bool:
        return True


_initialized = False


def _build_config(settings: Settings) -> TelemetryConfig | None:
    connection_string = settings.app_insights_connection_string or os.getenv(
        "APPLICATIONINSIGHTS_CONNECTION_STRING"
    )
    if not connection_string:
        return None

    return TelemetryConfig(
        connection_string=connection_string,
        service_name=settings.otel_service_name or "pb-sharepoint-agent",
        service_version=settings.otel_service_version or "0.1.0",
        environment=os.getenv("AZURE_ENVIRONMENT", "dev"),
        capture_message_content=settings.otel_capture_message_content,
    )


def initialize_telemetry(settings: Settings) -> bool:
    global _initialized
    if _initialized:
        return True

    config = _build_config(settings)
    if not config:
        return False

    os.environ.setdefault("APPLICATIONINSIGHTS_CONNECTION_STRING", config.connection_string)

    resource = Resource.create(
        {
            ResourceAttributes.SERVICE_NAME: config.service_name,
            ResourceAttributes.SERVICE_VERSION: config.service_version,
            "deployment.environment": config.environment,
        }
    )

    configure_azure_monitor(resource=resource)

    tracer_provider = trace.get_tracer_provider()
    if hasattr(tracer_provider, "add_span_processor"):
        tracer_provider.add_span_processor(AgentDimensionSpanProcessor(settings.sharepoint_agent_name))

    root_logger = logging.getLogger()
    if not any(isinstance(f, TraceContextFilter) for f in root_logger.filters):
        root_logger.addFilter(TraceContextFilter())

    try:
        AIProjectInstrumentor().instrument(enable_content_recording=config.capture_message_content)
    except Exception:  # pragma: no cover - defensive
        logging.getLogger(__name__).exception("telemetry_instrumentation_failed")

    _initialized = True
    return True
