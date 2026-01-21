from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List
import time

from openai import RateLimitError

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from invoice_assistant.config import get_settings
from invoice_assistant.core.logging import get_logger
from invoice_assistant.runtime.run import ask_with_metadata


def build_project_client() -> AIProjectClient:
    settings = get_settings()
    return AIProjectClient(
        endpoint=settings.azure_projects_endpoint,
        credential=DefaultAzureCredential(),
    )


def load_questions(path: Path) -> List[dict]:
    questions: List[dict] = []
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


def run_batch_questions(questions: Iterable[dict]) -> List[dict]:
    logger = get_logger(__name__)
    results: List[dict] = []
    questions = list(questions)

    logger.info("run_batch_questions count=%s", len(questions))

    for idx, item in enumerate(questions, start=1):
        question = item.get("question") if isinstance(item, dict) else str(item)
        result = None
        for attempt in range(1, 6):
            try:
                result = ask_with_metadata(question)
                break
            except RateLimitError:
                wait_seconds = min(2**attempt, 30)
                logger.warning(
                    "rate_limited retrying attempt=%s wait_seconds=%s",
                    attempt,
                    wait_seconds,
                )
                time.sleep(wait_seconds)
        if result is None:
            raise SystemExit("Rate limit retry exceeded.")
        context_snippets = [doc.snippet for doc in result.response.top_documents]
        logger.info(
            "batch_question_completed index=%s conversation_id=%s response_id=%s",
            idx,
            result.conversation_id,
            result.response_id,
        )
        results.append(
            {
                "question": question,
                "query": question,
                "response": result.response.answer,
                "context": "\n".join(context_snippets),
                "top_documents": [doc.model_dump() for doc in result.response.top_documents],
                "ground_truth": item.get("ground_truth") if isinstance(item, dict) else None,
                "expected_context": (
                    item.get("expected_context") if isinstance(item, dict) else None
                ),
                "conversation_id": result.conversation_id,
                "response_id": result.response_id,
            }
        )
    return results


def save_jsonl(records: Iterable[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")
