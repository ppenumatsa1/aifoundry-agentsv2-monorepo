from __future__ import annotations

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from teams_bing_agent.config import Settings
from teams_bing_agent.core.telemetry import initialize_telemetry


def build_project_client(settings: Settings) -> AIProjectClient:
    initialize_telemetry(settings)
    credential = DefaultAzureCredential(
        managed_identity_client_id=settings.managed_identity_client_id
    )
    return AIProjectClient(endpoint=settings.azure_projects_endpoint, credential=credential)
