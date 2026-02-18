from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from openai import APITimeoutError
from openai import BadRequestError
from openai import RateLimitError
from openai.types.responses.response_input_param import McpApprovalResponse, ResponseInputParam

from insurance_agent.config import get_settings
from insurance_agent.core.exceptions import McpApprovalRequiredError
from insurance_agent.core.logging import get_logger
from insurance_agent.core.prompt_loader import load_prompt_text
from insurance_agent.runtime.agent import get_or_create_agent
from insurance_agent.runtime.connections import ensure_project_connection
from insurance_agent.runtime.openai_client import build_project_client


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


def _extract_error_fields(error: BadRequestError) -> tuple[str, str, str]:
    text = str(error)
    code = ""
    message = ""

    body = getattr(error, "body", None)
    if isinstance(body, dict):
        inner = body.get("error")
        if isinstance(inner, dict):
            message = str(inner.get("message", ""))
            code = str(inner.get("code", ""))
    elif body is not None:
        inner = getattr(body, "error", None)
        if inner is not None:
            message = str(getattr(inner, "message", ""))
            code = str(getattr(inner, "code", ""))

    return text, code, message


def _is_mcp_tool_error(error: Exception) -> bool:
    if isinstance(error, APITimeoutError):
        return True

    if isinstance(error, RateLimitError):
        return True

    if not isinstance(error, BadRequestError):
        return False

    text, code, message = _extract_error_fields(error)
    text_l = text.lower()
    message_l = message.lower()

    if "mcp server" in text_l and "401" in text_l:
        return True

    if code == "tool_user_error":
        if "mcp server" in message_l:
            return True
        if "knowledge_base_retrieve" in message_l:
            return True
        if "failed dependency" in message_l:
            return True

    return False


def _fallback_answer_with_search_context(
    settings,
    openai_client,
    question: str,
) -> str:
    logger = get_logger(__name__)
    credential = DefaultAzureCredential()
    search_client = SearchClient(
        endpoint=settings.search_endpoint,
        index_name=settings.search_index_name,
        credential=credential,
    )

    results = search_client.search(
        search_text=question,
        top=settings.search_top_k,
        select=["content", "source", "chunk"],
    )

    context_blocks: list[str] = []
    for item in results:
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        source = str(item.get("source", "unknown"))
        chunk = str(item.get("chunk", ""))
        context_blocks.append(f"[{source}#{chunk}] {content[:1500]}")

    if not context_blocks:
        return "I couldn't retrieve relevant context from the knowledge index right now."

    grounded_prompt = (
        "You are an insurance assistant. Use only the provided context to answer the user question. "
        "If context is insufficient, say so clearly.\n\n"
        f"Question: {question}\n\n"
        "Context:\n" + "\n\n".join(context_blocks)
    )

    try:
        response = openai_client.responses.create(
            model=settings.azure_openai_model,
            input=grounded_prompt,
        )
        return _extract_response_text(response)
    except (RateLimitError, APITimeoutError) as exc:
        logger.warning("fallback_generation_rate_limited error=%s", exc)
        return (
            "I couldn't generate a fully synthesized answer right now due to service throttling. "
            "Here are the most relevant retrieved excerpts:\n\n" + "\n\n".join(context_blocks[:3])
        )


def _run_agent(question: str) -> tuple[str, str, str | None]:
    logger = get_logger(__name__)
    settings = get_settings()

    project_client = build_project_client(settings)
    prompt_text = load_prompt_text()
    instructions = prompt_text.strip()
    if settings.mcp_server_url:
        mcp_endpoint = settings.mcp_server_url
    else:
        base = settings.search_endpoint.rstrip("/")
        mcp_endpoint = (
            f"{base}/knowledgebases/{settings.knowledge_base_name}"
            f"/mcp?api-version=2025-11-01-Preview"
        )
    connection_id = ensure_project_connection(project_client, settings)

    with project_client.get_openai_client() as openai_client:
        request_client = openai_client.with_options(
            timeout=settings.response_timeout_seconds,
            max_retries=settings.response_max_retries,
        )

        agent_name = get_or_create_agent(
            project_client=project_client,
            settings=settings,
            instructions=instructions,
            connection_id=connection_id,
            server_url=mcp_endpoint,
        )
        logger.info("agent_ready name=%s", agent_name)

        conversation = openai_client.conversations.create()
        logger.info("conversation_created id=%s", conversation.id)

        logger.info("waiting_for_response")
        try:
            response = request_client.responses.create(
                conversation=conversation.id,
                tool_choice="required",
                input=question,
                extra_body={"agent": {"name": agent_name, "type": "agent_reference"}},
            )
            approval_rounds = 0
            while True:
                approval_input = _build_approval_input(
                    response.output,
                    server_label=settings.mcp_server_label,
                    auto_approve=settings.mcp_auto_approve,
                )
                if not approval_input:
                    break
                approval_rounds += 1
                if approval_rounds > settings.mcp_max_approval_rounds:
                    logger.warning(
                        "mcp_approval_round_limit_exceeded rounds=%s limit=%s using_fallback",
                        approval_rounds,
                        settings.mcp_max_approval_rounds,
                    )
                    fallback_text = _fallback_answer_with_search_context(
                        settings=settings,
                        openai_client=openai_client,
                        question=question,
                    )
                    return fallback_text, conversation.id, None
                if not settings.mcp_auto_approve:
                    logger.info("approval_required count=%s", len(approval_input))
                response = request_client.responses.create(
                    tool_choice="required",
                    input=approval_input,
                    previous_response_id=response.id,
                    extra_body={"agent": {"name": agent_name, "type": "agent_reference"}},
                )
        except (BadRequestError, RateLimitError, APITimeoutError) as exc:
            if _is_mcp_tool_error(exc):
                logger.warning("mcp_tool_failed_using_fallback error=%s", exc)
                fallback_text = _fallback_answer_with_search_context(
                    settings=settings,
                    openai_client=openai_client,
                    question=question,
                )
                return fallback_text, conversation.id, None
            raise

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


def ask_stream(question: str) -> Iterable[str]:
    response = ask(question)
    yield response
