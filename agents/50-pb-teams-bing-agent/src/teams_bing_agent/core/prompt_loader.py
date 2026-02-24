from __future__ import annotations

from pathlib import Path


def load_prompt_text() -> str:
    prompt_path = Path(__file__).resolve().parents[1] / "prompt.md"
    if not prompt_path.exists():
        return "You are a helpful Microsoft Teams assistant."
    return prompt_path.read_text(encoding="utf-8")
