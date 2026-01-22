from types import SimpleNamespace

from mcp_agent.runtime.agent import parse_require_approval
from mcp_agent.runtime.run import _extract_response_text
import pytest


@pytest.mark.unit
def test_parse_require_approval_allows_literals():
    assert parse_require_approval("always") == "always"
    assert parse_require_approval("never") == "never"


@pytest.mark.unit
def test_parse_require_approval_allows_json():
    value = '{"never":["tool_a"]}'
    parsed = parse_require_approval(value)
    assert parsed == {"never": ["tool_a"]}


@pytest.mark.unit
def test_parse_require_approval_rejects_invalid():
    with pytest.raises(Exception):
        parse_require_approval("maybe")


@pytest.mark.unit
def test_extract_response_text_prefers_output_text():
    response = SimpleNamespace(output_text="Hello", output=[])
    assert _extract_response_text(response) == "Hello"


@pytest.mark.unit
def test_extract_response_text_from_mcp_call_output():
    response = SimpleNamespace(
        output_text="",
        output=[
            SimpleNamespace(type="mcp_call", output='{"ok": true}'),
        ],
    )
    assert _extract_response_text(response) == '{"ok": true}'
