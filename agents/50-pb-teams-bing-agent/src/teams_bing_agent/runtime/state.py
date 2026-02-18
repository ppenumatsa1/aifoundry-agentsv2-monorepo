from __future__ import annotations

from threading import Lock


class ConversationStateStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._teams_to_foundry: dict[str, str] = {}

    def get_foundry_conversation_id(self, teams_conversation_id: str) -> str | None:
        with self._lock:
            return self._teams_to_foundry.get(teams_conversation_id)

    def set_foundry_conversation_id(
        self, teams_conversation_id: str, foundry_conversation_id: str
    ) -> None:
        with self._lock:
            self._teams_to_foundry[teams_conversation_id] = foundry_conversation_id
