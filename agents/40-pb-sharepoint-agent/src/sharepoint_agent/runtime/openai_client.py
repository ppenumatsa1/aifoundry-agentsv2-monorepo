from __future__ import annotations

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from sharepoint_agent.config import Settings
from sharepoint_agent.core.telemetry import initialize_telemetry


def build_project_client(settings: Settings) -> AIProjectClient:
    initialize_telemetry(settings)
    credential = DefaultAzureCredential()
    return AIProjectClient(endpoint=settings.azure_projects_endpoint, credential=credential)
