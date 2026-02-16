from __future__ import annotations

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    FileSearchTool,
    PromptAgentDefinition,
    PromptAgentDefinitionText,
    ResponseTextFormatConfigurationJsonSchema,
)

from invoice_assistant.core.schema_loader import schema_hash
from invoice_assistant.runtime.cache import load_agent_cache, save_agent_cache


def get_or_create_agent(
    project_client: AIProjectClient,
    agent_name: str,
    model: str,
    vector_store_id: str,
    schema: dict,
    instructions: str,
) -> str:
    cache = load_agent_cache()
    fingerprint = schema_hash(schema)

    agent_version = None
    if cache and cache.get("vector_store_id") == vector_store_id:
        if cache.get("schema_hash") == fingerprint:
            agent_version = cache.get("agent_version")
            agent_name = cache.get("agent_name", agent_name)

    if not agent_version:
        file_search = FileSearchTool(vector_store_ids=[vector_store_id])
        agent = project_client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=model,
                instructions=instructions,
                tools=[file_search],
                text=PromptAgentDefinitionText(
                    format=ResponseTextFormatConfigurationJsonSchema(
                        name="InvoiceAnswer",
                        schema=schema,
                        description="Answer invoice questions with citations.",
                    )
                ),
            ),
        )
        agent_version = agent.version
        save_agent_cache(agent.name, agent.version, vector_store_id, fingerprint)

    return agent_name
