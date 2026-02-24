from __future__ import annotations

import argparse


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Foundry eval scaffold for teams-bing-agent (not implemented yet)."
    )
    parser.add_argument(
        "--data",
        required=False,
        help="Path to captured evaluation dataset.",
    )
    return parser


def main() -> None:
    _ = build_arg_parser().parse_args()
    raise SystemExit(
        "run_foundry_evaluations.py is intentionally not implemented for pb-teams-bing-agent yet."
    )


if __name__ == "__main__":
    main()
