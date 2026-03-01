from __future__ import annotations

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from teams_bing_agent.config import Settings


def build_project_client(settings: Settings) -> AIProjectClient:
    credential = DefaultAzureCredential(
        managed_identity_client_id=settings.managed_identity_client_id
    )
    return AIProjectClient(endpoint=settings.azure_projects_endpoint, credential=credential)
