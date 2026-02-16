from __future__ import annotations

from typing import Any

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
import requests

from insurance_agent.config import Settings
from insurance_agent.core.exceptions import McpConfigError


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


def _build_arm_payload(settings: Settings, mcp_endpoint: str) -> dict[str, Any]:
    return {
        "name": settings.mcp_connection_name,
        "type": "Microsoft.MachineLearningServices/workspaces/connections",
        "properties": {
            "authType": "ProjectManagedIdentity",
            "category": "RemoteTool",
            "target": mcp_endpoint,
            "isSharedToAll": True,
            "isDefault": True,
            "audience": "https://search.azure.com/",
            "metadata": {"ApiType": "Azure", "server_label": settings.mcp_server_label},
        },
    }


def _create_or_update_arm_connection(settings: Settings, mcp_endpoint: str) -> str:
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

    payload = _build_arm_payload(settings, mcp_endpoint)
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.put(url, headers=headers, json=payload, timeout=30)
    if response.status_code not in (200, 201):
        raise McpConfigError(
            "Failed to create MCP project connection "
            f"(status={response.status_code}): {response.text}"
        )
    return settings.mcp_connection_name


def ensure_project_connection(project_client: AIProjectClient, settings: Settings) -> str:
    if settings.mcp_project_connection_id:
        return settings.mcp_project_connection_id

    base = settings.search_endpoint.rstrip("/")
    mcp_endpoint = (
        f"{base}/knowledgebases/{settings.knowledge_base_name}"
        f"/mcp?api-version=2025-11-01-Preview"
    )

    _create_or_update_arm_connection(settings, mcp_endpoint)
    return settings.mcp_connection_name
