from __future__ import annotations

from pathlib import Path


def load_prompt_text() -> str:
    prompt_path = Path(__file__).resolve().parents[1] / "prompt.md"
    return prompt_path.read_text(encoding="utf-8")
