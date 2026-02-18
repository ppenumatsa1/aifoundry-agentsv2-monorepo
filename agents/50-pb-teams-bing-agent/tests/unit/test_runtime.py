from types import SimpleNamespace

import pytest
from teams_bing_agent.runtime.run import _extract_response_text


@pytest.mark.unit
def test_extract_response_text_prefers_output_text() -> None:
    response = SimpleNamespace(output_text="hello", output=[])
    assert _extract_response_text(response) == "hello"


@pytest.mark.unit
def test_extract_response_text_from_message_blocks() -> None:
    response = SimpleNamespace(
        output_text="",
        output=[
            SimpleNamespace(
                type="message",
                content=[SimpleNamespace(type="output_text", text="from-block")],
            )
        ],
    )
    assert _extract_response_text(response) == "from-block"
