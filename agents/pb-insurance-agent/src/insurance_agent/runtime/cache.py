from __future__ import annotations

import json

from insurance_agent.core.paths import get_foundry_dir


def load_agent_cache() -> dict | None:
    agent_path = get_foundry_dir() / "agent.json"
    if not agent_path.exists():
        return None
    return json.loads(agent_path.read_text())


def save_agent_cache(agent_name: str, agent_version: str, tool_hash: str) -> None:
    output_dir = get_foundry_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "agent.json"
    output_path.write_text(
        json.dumps(
            {
                "agent_name": agent_name,
                "agent_version": agent_version,
                "tool_hash": tool_hash,
            },
            indent=2,
        )
    )


def load_connection_cache() -> dict | None:
    connection_path = get_foundry_dir() / "connection.json"
    if not connection_path.exists():
        return None
    return json.loads(connection_path.read_text())


def save_connection_cache(connection_id: str, connection_name: str) -> None:
    output_dir = get_foundry_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "connection.json"
    output_path.write_text(
        json.dumps(
            {
                "connection_id": connection_id,
                "connection_name": connection_name,
            },
            indent=2,
        )
    )
