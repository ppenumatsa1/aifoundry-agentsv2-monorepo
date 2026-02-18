from __future__ import annotations

import json
from pathlib import Path


def _get_foundry_dir() -> Path:
    project_root = Path(__file__).resolve().parents[3]
    return project_root / ".foundry"


def load_agent_cache() -> dict | None:
    agent_path = _get_foundry_dir() / "agent.json"
    if not agent_path.exists():
        return None
    return json.loads(agent_path.read_text())


def save_agent_cache(agent_name: str, agent_version: str, tool_hash: str) -> None:
    output_dir = _get_foundry_dir()
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
