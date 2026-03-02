from __future__ import annotations

from collections.abc import Iterable
import json
from pathlib import Path
import time

from teams_bing_agent.core.logging import get_logger
from teams_bing_agent.runtime.run import ask


def load_questions(path: Path) -> list[dict]:
    questions: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        if path.suffix.lower() == ".jsonl":
            row = json.loads(line)
            question = row.get("question") or row.get("prompt")
            if not question:
                raise SystemExit(f"Missing question in {path}: {line}")
            questions.append({**row, "question": str(question)})
        else:
            questions.append({"question": line})
    return questions


def run_batch_questions(questions: Iterable[dict]) -> list[dict]:
    logger = get_logger(__name__)
    results: list[dict] = []
    questions = list(questions)

    logger.info("run_batch_questions count=%s", len(questions))

    for idx, item in enumerate(questions, start=1):
        question = item.get("question") if isinstance(item, dict) else str(item)

        result = None
        for attempt in range(1, 6):
            try:
                result = ask(question)
                break
            except Exception as exc:  # pragma: no cover - network/service dependent
                message = str(exc).lower()
                if "rate" in message and "limit" in message:
                    wait_seconds = min(2**attempt, 30)
                    logger.warning(
                        "rate_limited retrying attempt=%s wait_seconds=%s",
                        attempt,
                        wait_seconds,
                    )
                    time.sleep(wait_seconds)
                    continue
                raise

        if result is None:
            raise SystemExit("Rate limit retry exceeded.")

        logger.info(
            "batch_question_completed index=%s response_id=%s",
            idx,
            result.response_id,
        )
        results.append(
            {
                "question": question,
                "query": question,
                "response": result.response_text,
                "context": item.get("context") if isinstance(item, dict) else None,
                "ground_truth": item.get("ground_truth") if isinstance(item, dict) else None,
                "expected_context": (
                    item.get("expected_context") if isinstance(item, dict) else None
                ),
                "response_id": result.response_id,
            }
        )

    return results


def save_jsonl(records: Iterable[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")
