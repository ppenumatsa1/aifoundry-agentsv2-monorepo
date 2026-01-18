from __future__ import annotations

from typing import Dict


def basic_exact_match(pred: dict, gold: dict) -> Dict[str, float]:
    return {
        "exact_match": 1.0 if pred == gold else 0.0,
    }
