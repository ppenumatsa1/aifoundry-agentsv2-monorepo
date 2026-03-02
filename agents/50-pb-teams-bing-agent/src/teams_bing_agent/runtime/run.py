from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from opentelemetry import trace

from teams_bing_agent.config import get_settings
from teams_bing_agent.core.exceptions import TeamsBingConfigError
from teams_bing_agent.core.logging import get_logger
from teams_bing_agent.core.prompt_loader import load_prompt_text
from teams_bing_agent.runtime.openai_client import build_project_client
from teams_bing_agent.runtime.agent import get_or_create_agent


@dataclass(frozen=True)
class AskResult:
    response_text: str
    response_id: str | None


logger = get_logger("teams_bing_agent.runtime.run")
tracer = trace.get_tracer(__name__)


def _extract_response_text(response: object) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output_items = getattr(response, "output", None)
    if not output_items:
        return ""

    parts: list[str] = []
    for item in output_items:
        item_type = getattr(item, "type", None)
        if item_type == "message":
            content = getattr(item, "content", None)
            if isinstance(content, list):
                for block in content:
                    if getattr(block, "type", None) == "output_text":
                        text = getattr(block, "text", None)
                        if isinstance(text, str) and text.strip():
                            parts.append(text.strip())
        elif item_type == "output_text":
            text = getattr(item, "text", None)
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())

    return "\n".join(parts).strip()


def _extract_tool_usage(response: object) -> list[str]:
    usage: list[str] = []
    output_items = getattr(response, "output", None)
    if not output_items:
        return usage

    for item in output_items:
        item_type = str(getattr(item, "type", "")).lower()
        if "search" in item_type:
            usage.append(item_type)
        elif "tool" in item_type:
            usage.append(item_type)

    return sorted(set(usage))


def ask(question: str) -> AskResult:
    settings = get_settings()
    if not settings.azure_projects_endpoint:
        raise TeamsBingConfigError("AZURE_AI_PROJECT_ENDPOINT must be set")

    project_client = build_project_client(settings)
    instructions = load_prompt_text()
    agent_name = get_or_create_agent(project_client, settings, instructions)

    with project_client.get_openai_client() as openai_client:
        with tracer.start_as_current_span("foundry.responses.create") as span:
            span.set_attribute("gen_ai.system", "az.ai.agents")
            span.set_attribute("gen_ai.agent.name", agent_name)
            span.set_attribute("gen_ai.user.message.length", len(question or ""))
            start = datetime.now(UTC)
            try:
                response = openai_client.responses.create(
                    input=question,
                    extra_body={
                        "agent": {
                            "name": agent_name,
                            "type": "agent_reference",
                        }
                    },
                )
            except Exception as exc:
                logger.exception(
                    "foundry_call_failed",
                    extra={
                        "event": "foundry_call_failed",
                        "flow_stage": "foundry_invoke",
                        "agent_name": agent_name,
                        "success": False,
                        "error_type": type(exc).__name__,
                    },
                )
                raise

            elapsed_ms = int((datetime.now(UTC) - start).total_seconds() * 1000)
            response_id = getattr(response, "id", None)
            tool_usage = _extract_tool_usage(response)

            span.set_attribute("app.foundry.duration_ms", elapsed_ms)
            span.set_attribute("app.foundry.tool_usage.count", len(tool_usage))
            if response_id:
                span.set_attribute("gen_ai.response.id", response_id)
            if tool_usage:
                span.set_attribute("app.foundry.tool_usage", ",".join(tool_usage))

            logger.info(
                "foundry_call_completed",
                extra={
                    "event": "foundry_call_completed",
                    "flow_stage": "foundry_result",
                    "agent_name": agent_name,
                    "foundry_response_id": response_id,
                    "duration_ms": elapsed_ms,
                    "tool_usage_count": len(tool_usage),
                    "success": True,
                },
            )

            response_text = _extract_response_text(response) or "No response."

    return AskResult(
        response_text=response_text,
        response_id=response_id,
    )
