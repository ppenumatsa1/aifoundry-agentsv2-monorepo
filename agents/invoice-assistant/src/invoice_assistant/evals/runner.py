from __future__ import annotations

import json
from pathlib import Path
from typing import List

from invoice_assistant.runtime.run import ask
from invoice_assistant.evals.metrics import basic_exact_match


def load_goldens(path: Path) -> List[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            rows.append(json.loads(line))
    return rows


def run_evals(goldens_path: Path) -> list[dict]:
    results = []
    for row in load_goldens(goldens_path):
        pred = ask(row["question"]).model_dump()
        metrics = basic_exact_match(pred, row["expected"])
        results.append({"question": row["question"], "metrics": metrics})
    return results
