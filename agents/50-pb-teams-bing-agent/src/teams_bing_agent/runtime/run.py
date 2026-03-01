from __future__ import annotations

from dataclasses import dataclass

from teams_bing_agent.config import get_settings
from teams_bing_agent.core.prompt_loader import load_prompt_text
from teams_bing_agent.runtime.openai_client import build_project_client
from teams_bing_agent.runtime.agent import get_or_create_agent


@dataclass(frozen=True)
class AskResult:
    response_text: str
    response_id: str | None


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


def ask(question: str) -> AskResult:
    settings = get_settings()
    if not settings.azure_projects_endpoint:
        raise ValueError("AZURE_AI_PROJECT_ENDPOINT must be set")

    project_client = build_project_client(settings)
    instructions = load_prompt_text()
    agent_name = get_or_create_agent(project_client, settings, instructions)

    with project_client.get_openai_client() as openai_client:
        response = openai_client.responses.create(
            input=question,
            extra_body={
                "agent": {
                    "name": agent_name,
                    "type": "agent_reference",
                }
            },
        )

        response_text = _extract_response_text(response) or "No response."
        response_id = getattr(response, "id", None)

    return AskResult(
        response_text=response_text,
        response_id=response_id,
    )
