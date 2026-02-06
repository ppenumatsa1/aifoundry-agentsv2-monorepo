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
        default="pb-insurance-agent",
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

    # Agent model
    azure_openai_model: str = Field(
        validation_alias=AliasChoices(
            "AZURE_AI_MODEL_DEPLOYMENT_NAME",
        )
    )

    azure_openai_endpoint: str = Field(
        validation_alias=AliasChoices(
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_RESOURCE_ENDPOINT",
            "azure_openai_endpoint",
        )
    )
    azure_openai_api_version: str = Field(
        default="2024-05-01-preview",
        validation_alias=AliasChoices(
            "AZURE_OPENAI_API_VERSION",
            "azure_openai_api_version",
        ),
    )

    # Embeddings
    embedding_model: str = Field(
        default="text-embed-3-large",
        validation_alias=AliasChoices("EMBEDDING_MODEL", "embedding_model"),
    )

    # Azure AI Search
    search_endpoint: str = Field(
        validation_alias=AliasChoices("SEARCH_ENDPOINT", "search_endpoint")
    )
    search_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SEARCH_API_KEY", "search_api_key"),
    )
    search_index_name: str = Field(
        validation_alias=AliasChoices("SEARCH_INDEX_NAME", "search_index_name")
    )
    knowledge_source_name: str = Field(
        default="insurance-knowledge-source",
        validation_alias=AliasChoices(
            "KNOWLEDGE_SOURCE_NAME",
            "AZURE_SEARCH_KNOWLEDGE_SOURCE_NAME",
            "knowledge_source_name",
        ),
    )
    knowledge_base_name: str = Field(
        default="insurance-knowledge-base",
        validation_alias=AliasChoices(
            "KNOWLEDGE_BASE_NAME",
            "AZURE_SEARCH_KNOWLEDGE_BASE_NAME",
            "knowledge_base_name",
        ),
    )
    search_top_k: int = Field(
        default=5, validation_alias=AliasChoices("SEARCH_TOP_K", "search_top_k")
    )
    search_vector_dim: int = Field(
        default=3072,
        validation_alias=AliasChoices("SEARCH_VECTOR_DIM", "search_vector_dim"),
    )
    chunk_size: int = Field(
        default=1000, validation_alias=AliasChoices("CHUNK_SIZE", "chunk_size")
    )
    chunk_overlap: int = Field(
        default=200, validation_alias=AliasChoices("CHUNK_OVERLAP", "chunk_overlap")
    )

    # MCP tool
    mcp_server_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("MCP_SERVER_URL", "mcp_server_url"),
    )
    mcp_server_label: str = Field(
        default="foundry-iq",
        validation_alias=AliasChoices("MCP_SERVER_LABEL", "mcp_server_label"),
    )
    mcp_connection_name: str = Field(
        default="foundry-iq-connection",
        validation_alias=AliasChoices("MCP_CONNECTION_NAME", "mcp_connection_name"),
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
        default="knowledge_base_retrieve",
        validation_alias=AliasChoices("MCP_ALLOWED_TOOLS", "mcp_allowed_tools"),
    )
    mcp_auto_approve: bool = Field(
        default=True,
        validation_alias=AliasChoices("MCP_AUTO_APPROVE", "mcp_auto_approve"),
    )
    insurance_agent_name: str = Field(
        default="pb-insurance-agent",
        validation_alias=AliasChoices("INSURANCE_AGENT_NAME", "insurance_agent_name"),
    )


def get_settings() -> Settings:
    return Settings()
