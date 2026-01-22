from mcp_agent.config import get_settings
from mcp_agent.runtime.run import ask
import pytest


@pytest.mark.integration
def test_ask_smoke():
    settings = get_settings()

    if (
        not settings.azure_projects_endpoint
        or not settings.azure_openai_model
        or not settings.mcp_server_url
    ):
        pytest.skip("Missing Azure or MCP environment variables")

    response = ask("What is my username in GitHub profile?")
    assert response
