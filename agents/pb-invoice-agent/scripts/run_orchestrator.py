from __future__ import annotations

from pathlib import Path
import subprocess
import time

from invoice_assistant.core.logging import get_logger

ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"

QUESTIONS_PATH = ROOT_DIR / "src/invoice_assistant/evals/datasets/questions.jsonl"
CAPTURE_PATH = ROOT_DIR / "src/invoice_assistant/evals/datasets/golden_capture.jsonl"
EVALUATION_NAME = "invoice-assistant-agent-eval"
SMOKE_QUESTION = "What is the total amount for invoice INV-1001?"


def run_step(logger, label: str, args: list[str]) -> None:
    cmd = " ".join(args)
    logger.info("step=%s start cmd=%s", label, cmd)
    started = time.time()
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    duration = time.time() - started
    if result.stdout:
        logger.info("step=%s stdout=\n%s", label, result.stdout.strip())
    if result.stderr:
        logger.warning("step=%s stderr=\n%s", label, result.stderr.strip())
    logger.info("step=%s done duration=%.2fs", label, duration)


def main() -> None:
    logger = get_logger(__name__)

    run_step(
        logger,
        "ingest",
        [
            "python",
            str(SCRIPTS_DIR / "ingest_invoices.py"),
        ],
    )

    run_step(
        logger,
        "agent_create",
        [
            "python",
            str(SCRIPTS_DIR / "run_agent.py"),
            SMOKE_QUESTION,
        ],
    )

    run_step(
        logger,
        "batch_questions",
        [
            "python",
            str(SCRIPTS_DIR / "run_batch_questions.py"),
            "--questions",
            str(QUESTIONS_PATH),
            "--out",
            str(CAPTURE_PATH),
        ],
    )

    run_step(
        logger,
        "evaluations",
        [
            "python",
            str(SCRIPTS_DIR / "run_foundry_evaluations.py"),
            "--data",
            str(CAPTURE_PATH),
            "--evaluation-name",
            EVALUATION_NAME,
        ],
    )


if __name__ == "__main__":
    main()
