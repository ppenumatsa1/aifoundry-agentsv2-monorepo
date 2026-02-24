from __future__ import annotations

from collections.abc import Iterable
import json
from pathlib import Path
import uuid

from azure.ai.projects import AIProjectClient
from dotenv import load_dotenv

from teams_bing_agent.config import get_settings
from teams_bing_agent.runtime.openai_client import build_project_client as _build_project_client
from teams_bing_agent.runtime.activityprotocol_client import send_activity_message

ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")


def build_project_client() -> AIProjectClient:
    settings = get_settings()
    return _build_project_client(settings)


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
    results: list[dict] = []

    for item in questions:
        question = item.get("question") if isinstance(item, dict) else str(item)
        teams_conversation_id = f"batch-{uuid.uuid4()}"

        result = send_activity_message(text=question, conversation_id=teams_conversation_id)

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
                "conversation_id": result.conversation_id,
                "response_id": None,
            }
        )
    return results


def save_jsonl(records: Iterable[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")
