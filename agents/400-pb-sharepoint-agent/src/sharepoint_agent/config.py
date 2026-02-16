from __future__ import annotations

from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    _env_path = Path(__file__).resolve().parents[2] / ".env"
    model_config = SettingsConfigDict(
        env_file=_env_path,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application Insights / Azure Monitor
    app_insights_connection_string: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "APP_INSIGHTS_CONNECTION_STRING", "app_insights_connection_string"
        ),
    )
    otel_service_name: str = Field(
        default="pb-sharepoint-agent",
        validation_alias=AliasChoices("OTEL_SERVICE_NAME", "otel_service_name"),
    )
    otel_service_version: str = Field(
        default="0.1.0",
        validation_alias=AliasChoices("OTEL_SERVICE_VERSION", "otel_service_version"),
    )
    otel_capture_message_content: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "OTEL_CAPTURE_MESSAGE_CONTENT", "otel_capture_message_content"
        ),
    )

    # Azure AI Projects
    azure_projects_endpoint: str = Field(
        validation_alias=AliasChoices(
            "AZURE_AI_PROJECT_ENDPOINT",
        )
    )
    azure_project_resource_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "AZURE_PROJECT_RESOURCE_ID",
            "AZURE_AI_PROJECT_RESOURCE_ID",
            "azure_project_resource_id",
        ),
    )

    # Azure OpenAI (Responses API)
    azure_openai_model: str = Field(
        validation_alias=AliasChoices(
            "AZURE_AI_MODEL_DEPLOYMENT_NAME",
        )
    )

    # SharePoint grounding tool
    sharepoint_connection_id: str = Field(
        validation_alias=AliasChoices("SHAREPOINT_CONNECTION_ID", "sharepoint_connection_id")
    )
    sharepoint_agent_name: str = Field(
        default="pb-sharepoint-agent",
        validation_alias=AliasChoices("SHAREPOINT_AGENT_NAME", "sharepoint_agent_name"),
    )


def get_settings() -> Settings:
    return Settings()
