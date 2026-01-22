from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import time

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from mcp_agent.core.logging import get_logger  # type: ignore[import-not-found]  # noqa: E402

SCRIPTS_DIR = ROOT_DIR / "scripts"
PYTHON = sys.executable or "python3"

QUESTIONS_PATH = ROOT_DIR / "src/mcp_agent/evals/datasets/questions.jsonl"
CAPTURE_PATH = ROOT_DIR / "src/mcp_agent/evals/datasets/golden_capture.jsonl"
EVALUATION_NAME = "mcp-agent-eval"
SMOKE_QUESTION = "What is my username in GitHub profile?"


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
        "agent_create",
        [
            PYTHON,
            str(SCRIPTS_DIR / "run_agent.py"),
            SMOKE_QUESTION,
        ],
    )

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
