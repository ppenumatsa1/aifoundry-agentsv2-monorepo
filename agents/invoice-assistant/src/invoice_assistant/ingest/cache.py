from __future__ import annotations

import json
from pathlib import Path

from invoice_assistant.core.paths import get_foundry_dir


def load_cached_vector_store_id() -> str | None:
    cache_path = get_foundry_dir() / "vector_store.json"
    if not cache_path.exists():
        return None
    data = json.loads(cache_path.read_text())
    return data.get("vector_store_id")


def save_vector_store_id(vector_store_id: str) -> None:
    output_dir = get_foundry_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "vector_store.json"
    output_path.write_text(json.dumps({"vector_store_id": vector_store_id}, indent=2))
