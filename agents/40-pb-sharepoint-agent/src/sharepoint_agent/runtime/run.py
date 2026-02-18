from __future__ import annotations

from dataclasses import dataclass

from sharepoint_agent.config import get_settings
from sharepoint_agent.core.logging import get_logger
from sharepoint_agent.core.prompt_loader import load_prompt_text
from sharepoint_agent.runtime.agent import get_or_create_agent
from sharepoint_agent.runtime.connections import ensure_project_connection
from sharepoint_agent.runtime.openai_client import build_project_client


@dataclass(frozen=True)
class AskResult:
    response_text: str
    conversation_id: str
    response_id: str | None


def _extract_response_text(response: object) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text

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
                        block_text = getattr(block, "text", None)
                        if isinstance(block_text, str) and block_text.strip():
                            parts.append(block_text)
        elif item_type == "output_text":
            block_text = getattr(item, "text", None)
            if isinstance(block_text, str) and block_text.strip():
                parts.append(block_text)
        elif item_type in {"tool_call", "tool_result"}:
            call_output = getattr(item, "output", None)
            if isinstance(call_output, str) and call_output.strip():
                parts.append(call_output)

    return "\n".join(parts).strip()


def _run_agent(question: str) -> tuple[str, str, str | None]:
    logger = get_logger(__name__)
    settings = get_settings()

    project_client = build_project_client(settings)
    prompt_text = load_prompt_text()
    instructions = prompt_text.strip()
    connection_id = ensure_project_connection(settings)

    with project_client.get_openai_client() as openai_client:
        agent_name = get_or_create_agent(
            project_client=project_client,
            settings=settings,
            instructions=instructions,
            connection_id=connection_id,
        )
        logger.info("agent_ready name=%s", agent_name)

        conversation = openai_client.conversations.create()
        logger.info("conversation_created id=%s", conversation.id)

        logger.info("waiting_for_response")
        response = openai_client.responses.create(
            conversation=conversation.id,
            input=question,
            extra_body={"agent": {"name": agent_name, "type": "agent_reference"}},
        )

        response_text = _extract_response_text(response)
        response_id = getattr(response, "id", None)
        return response_text, conversation.id, response_id


def ask(question: str) -> str:
    response_text, _, _ = _run_agent(question)
    return response_text


def ask_with_metadata(question: str) -> AskResult:
    response_text, conversation_id, response_id = _run_agent(question)
    return AskResult(
        response_text=response_text,
        conversation_id=conversation_id,
        response_id=response_id,
    )
