from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import time

ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"
PYTHON = sys.executable or "python3"

QUESTIONS_PATH = ROOT_DIR / "src/teams_bing_agent/evals/datasets/questions.jsonl"
CAPTURE_PATH = ROOT_DIR / "src/teams_bing_agent/evals/datasets/golden_capture.jsonl"
EVALUATION_NAME = "pb-teams-bing-agent-eval"


def _run_step(label: str, args: list[str]) -> None:
    cmd = " ".join(args)
    print(f"\n=== {label} ===")
    print(f"$ {cmd}")
    started = time.time()
    result = subprocess.run(args, check=False, capture_output=True, text=True)
    duration = time.time() - started
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())
    if result.returncode != 0:
        raise SystemExit(f"Step failed: {label} (exit={result.returncode})")
    print(f"Completed {label} in {duration:.2f}s")


def main() -> None:
    _run_step(
        "smoke-anon",
        [
            PYTHON,
            str(SCRIPTS_DIR / "run_anon_smoke_test.py"),
        ],
    )

    _run_step(
        "batch",
        [
            PYTHON,
            str(SCRIPTS_DIR / "run_batch_questions.py"),
            "--questions",
            str(QUESTIONS_PATH),
            "--out",
            str(CAPTURE_PATH),
        ],
    )

    _run_step(
        "evals",
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
