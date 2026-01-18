from __future__ import annotations

import json

from invoice_assistant.core.exceptions import VectorStoreNotFoundError
from invoice_assistant.core.paths import get_foundry_dir


def load_vector_store_id() -> str:
    cache_path = get_foundry_dir() / "vector_store.json"
    if not cache_path.exists():
        raise VectorStoreNotFoundError(
            "Vector store id not found. Run: python scripts/ingest_invoices.py"
        )
    data = json.loads(cache_path.read_text())
    return data["vector_store_id"]


def load_agent_cache() -> dict | None:
    agent_path = get_foundry_dir() / "agent.json"
    if not agent_path.exists():
        return None
    return json.loads(agent_path.read_text())


def save_agent_cache(
    agent_name: str, agent_version: str, vector_store_id: str, schema_hash: str
) -> None:
    output_dir = get_foundry_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "agent.json"
    output_path.write_text(
        json.dumps(
            {
                "agent_name": agent_name,
                "agent_version": agent_version,
                "vector_store_id": vector_store_id,
                "schema_hash": schema_hash,
            },
            indent=2,
        )
    )
