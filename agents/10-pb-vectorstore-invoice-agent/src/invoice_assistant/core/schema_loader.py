from __future__ import annotations

import json
from pathlib import Path


def load_response_schema() -> dict:
    schema_path = Path(__file__).resolve().parents[1] / "schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def schema_hash(schema: dict) -> str:
    payload = json.dumps(schema, sort_keys=True).encode("utf-8")
    import hashlib

    return hashlib.sha256(payload).hexdigest()
