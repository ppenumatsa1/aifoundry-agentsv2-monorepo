from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import json

from invoice_assistant.config import get_settings
from invoice_assistant.core.logging import get_logger
from invoice_assistant.core.prompt_loader import load_prompt_text
from invoice_assistant.core.schema_loader import load_response_schema
from invoice_assistant.runtime.agent import get_or_create_agent
from invoice_assistant.runtime.cache import load_vector_store_id
from invoice_assistant.runtime.messages import build_instructions
from invoice_assistant.runtime.openai_client import build_project_client
from invoice_assistant.schema import InvoiceAssistantResponse


@dataclass(frozen=True)
class AskResult:
    response: InvoiceAssistantResponse
    conversation_id: str
    response_id: str | None


def _run_agent(question: str) -> tuple[InvoiceAssistantResponse, str, str | None]:
    logger = get_logger(__name__)
    settings = get_settings()
    model = settings.azure_openai_model
    agent_name = settings.invoice_agent_name

    vector_store_id = load_vector_store_id()
    schema = load_response_schema()

    project_client = build_project_client(settings)

    prompt_text = load_prompt_text()
    instructions = build_instructions(prompt_text, schema)

    with project_client.get_openai_client() as openai_client:
        agent_name = get_or_create_agent(
            project_client=project_client,
            agent_name=agent_name,
            model=model,
            vector_store_id=vector_store_id,
            schema=schema,
            instructions=instructions,
        )
        logger.info("agent_ready name=%s", agent_name)

        conversation = openai_client.conversations.create(
            items=[{"type": "message", "role": "user", "content": question}]
        )

        logger.info("waiting_for_response")
        response = openai_client.responses.create(
            conversation=conversation.id,
            input="",
            extra_body={"agent": {"name": agent_name, "type": "agent_reference"}},
        )
        logger.info("response_received")

        response_text = response.output_text
        data = json.loads(response_text)
        response_id = getattr(response, "id", None)
        return InvoiceAssistantResponse.model_validate(data), conversation.id, response_id


def ask(question: str, stream: bool = False) -> InvoiceAssistantResponse:
    response, _, _ = _run_agent(question)
    return response


def ask_with_metadata(question: str) -> AskResult:
    response, conversation_id, response_id = _run_agent(question)
    return AskResult(
        response=response,
        conversation_id=conversation_id,
        response_id=response_id,
    )


def ask_stream(question: str) -> Iterable[str]:
    response = ask(question, stream=False)
    yield response.model_dump_json()
