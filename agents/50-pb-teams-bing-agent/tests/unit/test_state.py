import pytest
from teams_bing_agent.runtime.state import ConversationStateStore


@pytest.mark.unit
def test_state_store_roundtrip() -> None:
    store = ConversationStateStore()
    assert store.get_foundry_conversation_id("teams-1") is None

    store.set_foundry_conversation_id("teams-1", "foundry-1")
    assert store.get_foundry_conversation_id("teams-1") == "foundry-1"
