from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from openai.types.responses.response_input_param import McpApprovalResponse, ResponseInputParam

from mcp_agent.config import get_settings
from mcp_agent.core.exceptions import McpApprovalRequiredError
from mcp_agent.core.logging import get_logger
from mcp_agent.core.prompt_loader import load_prompt_text
from mcp_agent.runtime.agent import get_or_create_agent
from mcp_agent.runtime.connections import ensure_project_connection
from mcp_agent.runtime.openai_client import build_project_client


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
        elif item_type in {"mcp_call", "mcp_result"}:
            call_output = getattr(item, "output", None)
            if isinstance(call_output, str) and call_output.strip():
                parts.append(call_output)

    return "\n".join(parts).strip()


def _build_approval_input(
    output_items: Iterable[object],
    server_label: str,
    auto_approve: bool,
) -> ResponseInputParam:
    input_list: list[McpApprovalResponse] = []
    for item in output_items:
        if getattr(item, "type", None) != "mcp_approval_request":
            continue
        approval_id = getattr(item, "id", None)
        item_label = getattr(item, "server_label", None)
        if item_label and item_label != server_label:
            continue
        if not approval_id:
            continue
        if not auto_approve:
            raise McpApprovalRequiredError("MCP approval required but auto-approve is disabled")
        input_list.append(
            McpApprovalResponse(
                type="mcp_approval_response",
                approve=True,
                approval_request_id=approval_id,
            )
        )
    return input_list


def _run_agent(question: str) -> tuple[str, str, str | None]:
    logger = get_logger(__name__)
    settings = get_settings()

    project_client = build_project_client(settings)
    prompt_text = load_prompt_text()
    instructions = prompt_text.strip()
    connection_id = ensure_project_connection(project_client, settings)

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

        while True:
            approval_input = _build_approval_input(
                response.output,
                server_label=settings.mcp_server_label,
                auto_approve=settings.mcp_auto_approve,
            )
            if not approval_input:
                break
            if not settings.mcp_auto_approve:
                logger.info("approval_required count=%s", len(approval_input))
            response = openai_client.responses.create(
                input=approval_input,
                previous_response_id=response.id,
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
