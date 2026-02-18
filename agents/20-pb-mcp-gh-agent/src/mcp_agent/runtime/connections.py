from __future__ import annotations

from typing import Any

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
import requests

from mcp_agent.config import Settings
from mcp_agent.core.exceptions import McpConfigError
from mcp_agent.runtime.cache import load_connection_cache, save_connection_cache


def _build_arm_payload(settings: Settings) -> dict[str, Any]:
    if not settings.mcp_pat:
        raise McpConfigError("MCP_PAT is required to create a project connection")
    if not settings.mcp_server_url:
        raise McpConfigError("MCP_SERVER_URL is required to create a project connection")

    auth_header = "Authorization"
    token_value = settings.mcp_pat.strip()
    properties: dict[str, Any] = {
        "authType": "CustomKeys",
        "category": "RemoteTool",
        "target": settings.mcp_server_url,
        "isSharedToAll": True,
        "metadata": {"server_label": settings.mcp_server_label},
        "credentials": {"keys": {auth_header: f"Bearer {token_value}"}},
    }

    return {
        "name": settings.mcp_connection_name,
        "type": "Microsoft.MachineLearningServices/workspaces/connections",
        "properties": properties,
    }


def _extract_connection_id(payload: dict[str, Any]) -> str | None:
    for key in ("id", "connectionId", "connection_id"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    properties = payload.get("properties")
    if isinstance(properties, dict):
        for key in ("connectionId", "connection_id"):
            value = properties.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return None


def _create_arm_connection(settings: Settings) -> str:
    if not settings.azure_project_resource_id:
        raise McpConfigError("AZURE_PROJECT_RESOURCE_ID is required to create a project connection")

    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(credential, "https://management.azure.com/.default")
    token = token_provider()

    api_version = "2025-10-01-preview"
    resource_id = settings.azure_project_resource_id.rstrip("/")
    url = (
        f"https://management.azure.com{resource_id}/connections/"
        f"{settings.mcp_connection_name}?api-version={api_version}"
    )

    payload = _build_arm_payload(settings)
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.put(url, headers=headers, json=payload, timeout=30)
    if response.status_code not in (200, 201):
        raise McpConfigError(
            "Failed to create MCP project connection "
            f"(status={response.status_code}): {response.text}"
        )

    data = response.json() if response.text else {}
    connection_id = _extract_connection_id(data) or settings.mcp_connection_name
    save_connection_cache(connection_id, settings.mcp_connection_name)
    return connection_id


def ensure_project_connection(project_client: AIProjectClient, settings: Settings) -> str:
    if settings.mcp_project_connection_id:
        return settings.mcp_project_connection_id

    cached = load_connection_cache()
    if cached:
        cached_id = cached.get("connection_id")
        cached_name = cached.get("connection_name")
        if cached_id and cached_name == settings.mcp_connection_name:
            return cached_id

    if settings.azure_project_resource_id:
        return _create_arm_connection(settings)

    try:
        connection = project_client.connections.get(settings.mcp_connection_name)
    except Exception as exc:  # pragma: no cover - network
        raise McpConfigError(
            "MCP project connection not found. Create the connection in Foundry or set "
            "AZURE_PROJECT_RESOURCE_ID for ARM creation."
        ) from exc

    payload = dict(connection) if hasattr(connection, "items") else {}
    connection_id = _extract_connection_id(payload) or settings.mcp_connection_name
    save_connection_cache(connection_id, settings.mcp_connection_name)
    return connection_id
