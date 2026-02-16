from __future__ import annotations

from pathlib import Path


def get_agent_root() -> Path:
    return Path(__file__).resolve().parents[3]


def get_foundry_dir() -> Path:
    return get_agent_root() / ".foundry"
