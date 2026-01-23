import argparse
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from insurance_agent.core.logging import get_logger  # type: ignore[import-not-found]  # noqa: E402
from insurance_agent.evals.batch import (  # type: ignore[import-not-found]  # noqa: E402
    load_questions,
    run_batch_questions,
    save_jsonl,
)

DEFAULT_QUESTIONS_PATH = ROOT_DIR / "src/insurance_agent/evals/datasets/questions.jsonl"
DEFAULT_CAPTURE_PATH = ROOT_DIR / "src/insurance_agent/evals/datasets/golden_capture.jsonl"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run batch questions and capture response IDs.")
    parser.add_argument(
        "--questions",
        default=str(DEFAULT_QUESTIONS_PATH),
        help="Path to questions.jsonl",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_CAPTURE_PATH),
        help="Output path for golden_capture.jsonl",
    )
    return parser


def main() -> None:
    logger = get_logger(__name__)
    args = build_arg_parser().parse_args()
    questions_path = Path(args.questions)
    output_path = Path(args.out)

    if not questions_path.exists():
        raise SystemExit(f"Questions file not found: {questions_path}")

    questions = load_questions(questions_path)
    if not questions:
        raise SystemExit("No questions found for evaluation.")

    results = run_batch_questions(questions)
    save_jsonl(results, output_path)

    logger.info(
        "captured_batch_questions questions=%s output=%s",
        len(results),
        str(output_path),
    )

    print(f"Captured {len(results)} runs -> {output_path}")


if __name__ == "__main__":
    main()
