from insurance_agent.config import Settings


def test_settings_load_without_provisioning_env_vars() -> None:
    settings = Settings(
        _env_file=None,
        AZURE_AI_PROJECT_ENDPOINT="https://example.services.ai.azure.com/api/projects/example-proj",
        AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4.1-mini",
        AZURE_OPENAI_ENDPOINT="https://example-foundry.cognitiveservices.azure.com",
        SEARCH_ENDPOINT="https://example-search.search.windows.net",
        SEARCH_INDEX_NAME="insurance-knowledge",
    )

    assert settings.search_endpoint == "https://example-search.search.windows.net"
    assert settings.search_index_name == "insurance-knowledge"
    assert settings.azure_openai_model == "gpt-4.1-mini"
