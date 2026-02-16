from types import SimpleNamespace

import pytest
from sharepoint_agent.config import Settings
from sharepoint_agent.core.exceptions import SharepointConfigError
from sharepoint_agent.runtime.connections import ensure_project_connection
from sharepoint_agent.runtime.run import _extract_response_text


@pytest.mark.unit
def test_extract_response_text_prefers_output_text():
    response = SimpleNamespace(output_text="Hello", output=[])
    assert _extract_response_text(response) == "Hello"


@pytest.mark.unit
def test_extract_response_text_from_tool_result_output():
    response = SimpleNamespace(
        output_text="",
        output=[
            SimpleNamespace(type="tool_result", output='{"ok": true}'),
        ],
    )
    assert _extract_response_text(response) == '{"ok": true}'


@pytest.mark.unit
def test_ensure_project_connection_accepts_valid_arm_id():
    settings = Settings.model_construct(
        sharepoint_connection_id=(
            "/subscriptions/00000000-0000-0000-0000-000000000000/"
            "resourceGroups/rg/providers/Microsoft.MachineLearningServices/"
            "workspaces/ws/connections/sharepoint-docs"
        )
    )
    assert ensure_project_connection(settings).endswith("/connections/sharepoint-docs")


@pytest.mark.unit
def test_ensure_project_connection_rejects_non_arm_values():
    settings = Settings.model_construct(sharepoint_connection_id="sharepoint-docs")
    with pytest.raises(SharepointConfigError):
        ensure_project_connection(settings)
