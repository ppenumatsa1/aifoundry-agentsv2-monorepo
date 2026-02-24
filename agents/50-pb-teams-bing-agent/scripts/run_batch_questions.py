from __future__ import annotations

import argparse


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Batch scaffold for teams-bing-agent (not implemented yet)."
    )
    parser.add_argument(
        "--questions",
        required=False,
        help="Path to questions dataset.",
    )
    return parser


def main() -> None:
    _ = build_arg_parser().parse_args()
    raise SystemExit(
        "run_batch_questions.py is intentionally not implemented for pb-teams-bing-agent yet."
    )


if __name__ == "__main__":
    main()
