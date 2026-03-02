from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    _env_path = Path(__file__).resolve().parents[2] / ".env"
    model_config = SettingsConfigDict(
        env_file=_env_path,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_insights_connection_string: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "APP_INSIGHTS_CONNECTION_STRING",
            "app_insights_connection_string",
        ),
    )
    otel_service_name: str = Field(
        default="pb-teams-bing-agent",
        validation_alias=AliasChoices("OTEL_SERVICE_NAME", "otel_service_name"),
    )
    otel_service_version: str = Field(
        default="0.1.0",
        validation_alias=AliasChoices("OTEL_SERVICE_VERSION", "otel_service_version"),
    )
    otel_capture_message_content: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "OTEL_CAPTURE_MESSAGE_CONTENT",
            "otel_capture_message_content",
        ),
    )

    microsoft_app_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("MICROSOFT_APP_ID"),
    )
    microsoft_app_password: str | None = Field(
        default=None,
        validation_alias=AliasChoices("MICROSOFT_APP_PASSWORD"),
    )
    microsoft_app_tenant_id: str | None = Field(default=None)
    microsoft_app_type: Literal["SingleTenant", "MultiTenant"] = Field(default="SingleTenant")

    managed_identity_client_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("MANAGED_IDENTITY_CLIENT_ID"),
    )

    azure_projects_endpoint: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "AZURE_AI_PROJECT_ENDPOINT",
            "PROJECT_ENDPOINT",
        ),
    )
    azure_project_resource_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AZURE_PROJECT_RESOURCE_ID"),
    )
    foundry_agent_id: str | None = Field(
        default="pb-teams-bing-agent",
        validation_alias=AliasChoices(
            "FOUNDRY_AGENT_ID",
            "foundry_agent_id",
        ),
    )
    azure_openai_model: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "AZURE_AI_MODEL_DEPLOYMENT_NAME",
        ),
    )
    web_search_context_size: Literal["low", "medium", "high"] | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "WEB_SEARCH_CONTEXT_SIZE",
            "web_search_context_size",
        ),
    )
    web_search_country: str | None = Field(
        default=None,
        validation_alias=AliasChoices("WEB_SEARCH_COUNTRY", "web_search_country"),
    )
    web_search_region: str | None = Field(
        default=None,
        validation_alias=AliasChoices("WEB_SEARCH_REGION", "web_search_region"),
    )
    web_search_city: str | None = Field(
        default=None,
        validation_alias=AliasChoices("WEB_SEARCH_CITY", "web_search_city"),
    )
    web_search_timezone: str | None = Field(
        default=None,
        validation_alias=AliasChoices("WEB_SEARCH_TIMEZONE", "web_search_timezone"),
    )

    fastapi_host: str = Field(
        default="0.0.0.0",
        validation_alias=AliasChoices("FASTAPI_HOST", "fastapi_host"),
    )
    fastapi_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        validation_alias=AliasChoices("FASTAPI_PORT", "fastapi_port"),
    )

    @field_validator(
        "microsoft_app_id",
        "microsoft_app_password",
        "microsoft_app_tenant_id",
        "managed_identity_client_id",
        "azure_projects_endpoint",
        "azure_project_resource_id",
        "foundry_agent_id",
        "azure_openai_model",
        "web_search_country",
        "web_search_region",
        "web_search_city",
        "web_search_timezone",
        mode="before",
    )
    @classmethod
    def normalize_optional_strings(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @field_validator("web_search_context_size", mode="before")
    @classmethod
    def normalize_context_size(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip().lower()
            return stripped or None
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
