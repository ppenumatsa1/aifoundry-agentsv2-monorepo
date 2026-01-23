from __future__ import annotations

import hashlib
import json

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MCPTool, PromptAgentDefinition

from insurance_agent.config import Settings
from insurance_agent.core.exceptions import McpConfigError
from insurance_agent.runtime.cache import load_agent_cache, save_agent_cache


def _parse_allowed_tools(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    parts = [item.strip() for item in raw.split(",") if item.strip()]
    return parts or None


def parse_require_approval(raw: str) -> str | dict:
    value = (raw or "").strip()
    if value in {"always", "never"}:
        return value
    if value.startswith("{"):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise McpConfigError("Invalid MCP_REQUIRE_APPROVAL JSON") from exc
        if not isinstance(parsed, dict):
            raise McpConfigError("MCP_REQUIRE_APPROVAL JSON must be an object")
        return parsed
    raise McpConfigError("MCP_REQUIRE_APPROVAL must be 'always', 'never', or JSON")


def _tool_fingerprint(
    settings: Settings,
    instructions: str,
    connection_id: str,
    server_url: str,
) -> str:
    payload = {
        "server_url": server_url,
        "server_label": settings.mcp_server_label,
        "project_connection_id": connection_id,
        "require_approval": settings.mcp_require_approval,
        "allowed_tools": settings.mcp_allowed_tools,
        "instructions_hash": hashlib.sha256(instructions.encode("utf-8")).hexdigest(),
        "model": settings.azure_openai_model,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def get_or_create_agent(
    project_client: AIProjectClient,
    settings: Settings,
    instructions: str,
    connection_id: str,
    server_url: str,
) -> str:
    cache = load_agent_cache()
    tool_hash = _tool_fingerprint(settings, instructions, connection_id, server_url)

    agent_name = settings.insurance_agent_name
    agent_version = None
    if cache and cache.get("tool_hash") == tool_hash:
        agent_version = cache.get("agent_version")
        agent_name = cache.get("agent_name", agent_name)

    if not agent_version:
        tool = MCPTool(
            server_label=settings.mcp_server_label,
            server_url=server_url,
            require_approval=parse_require_approval(settings.mcp_require_approval),
            allowed_tools=_parse_allowed_tools(settings.mcp_allowed_tools),
            project_connection_id=None,  # Let it use default RemoteTool connection
        )
        agent = project_client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=settings.azure_openai_model,
                instructions=instructions,
                tools=[tool],
            ),
        )
        agent_version = agent.version
        save_agent_cache(agent.name, agent.version, tool_hash)

    return agent_name
