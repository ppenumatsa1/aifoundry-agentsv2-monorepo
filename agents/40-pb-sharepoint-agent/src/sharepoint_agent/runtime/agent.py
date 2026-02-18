from __future__ import annotations

import hashlib
import json

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    SharepointAgentTool,
    SharepointGroundingToolParameters,
    ToolProjectConnection,
)

from sharepoint_agent.config import Settings
from sharepoint_agent.runtime.cache import load_agent_cache, save_agent_cache


def _tool_fingerprint(settings: Settings, instructions: str, connection_id: str) -> str:
    payload = {
        "sharepoint_connection_id": connection_id,
        "instructions_hash": hashlib.sha256(instructions.encode("utf-8")).hexdigest(),
        "model": settings.azure_openai_model,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def get_or_create_agent(
    project_client: AIProjectClient,
    settings: Settings,
    instructions: str,
    connection_id: str,
) -> str:
    cache = load_agent_cache()
    tool_hash = _tool_fingerprint(settings, instructions, connection_id)

    agent_name = settings.sharepoint_agent_name
    agent_version = None
    if cache and cache.get("tool_hash") == tool_hash:
        agent_version = cache.get("agent_version")
        agent_name = cache.get("agent_name", agent_name)

    if not agent_version:
        tool = SharepointAgentTool(
            sharepoint_grounding_preview=SharepointGroundingToolParameters(
                project_connections=[ToolProjectConnection(project_connection_id=connection_id)]
            )
        )
        agent = project_client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=settings.azure_openai_model,
                instructions=instructions,
                tools=[tool],
            ),
        )
        save_agent_cache(agent.name, agent.version, tool_hash)

    return agent_name
