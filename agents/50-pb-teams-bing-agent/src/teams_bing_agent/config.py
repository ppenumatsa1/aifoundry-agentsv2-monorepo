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

    azure_projects_endpoint: str = Field(
        validation_alias=AliasChoices(
            "AZURE_AI_PROJECT_ENDPOINT",
            "PROJECT_ENDPOINT",
        )
    )
    foundry_agent_id: str = Field(
        validation_alias=AliasChoices(
            "FOUNDRY_AGENT_ID",
            "foundry_agent_id",
        )
    )
    azure_openai_model: str = Field(
        validation_alias=AliasChoices(
            "AZURE_AI_MODEL_DEPLOYMENT_NAME",
        )
    )
    web_search_context_size: str | None = Field(
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
        validation_alias=AliasChoices("FASTAPI_PORT", "fastapi_port"),
    )


def get_settings() -> Settings:
    return Settings()
