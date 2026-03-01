import pytest

from teams_bing_agent.config import Settings
from teams_bing_agent.runtime.agent import resolve_agent_name


@pytest.mark.unit
def test_resolve_agent_name_returns_value() -> None:
    settings = Settings(foundry_agent_id="published-agent")
    assert resolve_agent_name(settings) == "published-agent"


@pytest.mark.unit
def test_resolve_agent_name_requires_value() -> None:
    settings = Settings(foundry_agent_id=None)
    with pytest.raises(ValueError, match="FOUNDRY_AGENT_ID must be set"):
        resolve_agent_name(settings)
