from sharepoint_agent.config import get_settings
from sharepoint_agent.runtime.run import ask
import pytest


@pytest.mark.integration
def test_ask_smoke():
    try:
        settings = get_settings()
    except Exception:
        pytest.skip("Missing Azure or SharePoint environment variables")

    if (
        not settings.azure_projects_endpoint
        or not settings.azure_openai_model
        or not settings.sharepoint_connection_id
    ):
        pytest.skip("Missing Azure or SharePoint environment variables")

    response = ask("Summarize key security requirements from the connected SharePoint docs.")
    assert response
