from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    _env_path = Path(__file__).resolve().parents[2] / ".env"
    model_config = SettingsConfigDict(env_file=_env_path, env_file_encoding="utf-8")

    # Azure AI Projects
    azure_projects_endpoint: str
    # Azure OpenAI (Responses API)
    azure_openai_endpoint: str
    azure_openai_model: str
    azure_openai_api_version: str

    # Agent config
    invoice_dataset_name: str
    invoice_vectorstore_name: str
    invoice_agent_name: str
    invoice_top_k: int


def get_settings() -> Settings:
    return Settings()
