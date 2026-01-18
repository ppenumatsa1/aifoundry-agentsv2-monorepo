from __future__ import annotations

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from invoice_assistant.config import Settings


def build_project_client(settings: Settings) -> AIProjectClient:
    credential = DefaultAzureCredential()
    return AIProjectClient(
        endpoint=settings.azure_projects_endpoint, credential=credential
    )
