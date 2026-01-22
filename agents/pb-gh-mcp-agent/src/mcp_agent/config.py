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
        default="mcp-agent",
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
            "AZURE_PROJECTS_ENDPOINT",
            "FOUNDRY_PROJECT_ENDPOINT",
            "azure_projects_endpoint",
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
            "MODEL_DEPLOYMENT_NAME",
            "AZURE_OPENAI_MODEL",
            "azure_openai_model",
        )
    )

    # MCP tool
    mcp_server_url: str = Field(validation_alias=AliasChoices("MCP_SERVER_URL", "mcp_server_url"))
    mcp_server_label: str = Field(
        default="mcp-server",
        validation_alias=AliasChoices("MCP_SERVER_LABEL", "mcp_server_label"),
    )
    mcp_connection_name: str = Field(
        default="mcp-connection",
        validation_alias=AliasChoices("MCP_CONNECTION_NAME", "mcp_connection_name"),
    )
    mcp_pat: str | None = Field(
        default=None,
        validation_alias=AliasChoices("MCP_PAT", "mcp_pat"),
    )
    mcp_project_connection_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "MCP_PROJECT_CONNECTION_ID",
            "MCP_PROJECT_CONNECTION_NAME",
            "mcp_project_connection_id",
        ),
    )
    mcp_require_approval: str = Field(
        default="always",
        validation_alias=AliasChoices("MCP_REQUIRE_APPROVAL", "mcp_require_approval"),
    )
    mcp_allowed_tools: str | None = Field(
        default=None,
        validation_alias=AliasChoices("MCP_ALLOWED_TOOLS", "mcp_allowed_tools"),
    )
    mcp_auto_approve: bool = Field(
        default=True,
        validation_alias=AliasChoices("MCP_AUTO_APPROVE", "mcp_auto_approve"),
    )
    mcp_agent_name: str = Field(
        default="mcp-agent",
        validation_alias=AliasChoices("MCP_AGENT_NAME", "mcp_agent_name"),
    )


def get_settings() -> Settings:
    return Settings()
