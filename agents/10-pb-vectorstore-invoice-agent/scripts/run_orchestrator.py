from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import time

from invoice_assistant.core.logging import get_logger

ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"
PYTHON = sys.executable or "python3"

QUESTIONS_PATH = ROOT_DIR / "src/invoice_assistant/evals/datasets/questions.jsonl"
CAPTURE_PATH = ROOT_DIR / "src/invoice_assistant/evals/datasets/golden_capture.jsonl"
EVALUATION_NAME = "pb-vectorstore-invoice-agent-eval"
SMOKE_QUESTION = "What is the total amount for invoice INV-1001?"


def run_step(logger, label: str, args: list[str]) -> None:
    # Standardized wrapper so each step reports timing and stdout/stderr.
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


def log_section(logger, title: str) -> None:
    logger.info("")
    logger.info("==================== %s ====================", title)
    logger.info("")


def main() -> None:
    logger = get_logger(__name__)

    # Step 1: Ingest invoice documents into a vector store.
    log_section(logger, "Step 1: Ingest")
    run_step(
        logger,
        "ingest",
        [
            PYTHON,
            str(SCRIPTS_DIR / "ingest_invoices.py"),
        ],
    )

    # Step 2: Smoke test the agent with a single question.
    log_section(logger, "Step 2: Smoke test")
    run_step(
        logger,
        "agent_create",
        [
            PYTHON,
            str(SCRIPTS_DIR / "run_agent.py"),
            SMOKE_QUESTION,
        ],
    )

    # Step 3: Run the batch questions to capture traces.
    log_section(logger, "Step 3: Run Batch")
    run_step(
        logger,
        "batch_questions",
        [
            PYTHON,
            str(SCRIPTS_DIR / "run_batch_questions.py"),
            "--questions",
            str(QUESTIONS_PATH),
            "--out",
            str(CAPTURE_PATH),
        ],
    )

    # Step 4: Evaluate captured runs with Foundry evaluators.
    log_section(logger, "Step 4: Run Evaluations")
    run_step(
        logger,
        "evaluations",
        [
            PYTHON,
            str(SCRIPTS_DIR / "run_foundry_evaluations.py"),
            "--data",
            str(CAPTURE_PATH),
            "--evaluation-name",
            EVALUATION_NAME,
        ],
    )


if __name__ == "__main__":
    main()
