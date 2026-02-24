from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from teams_bing_agent.runtime.activityprotocol_client import (  # type: ignore[import-not-found]  # noqa: E402
    send_activity_message,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="One-turn smoke test for published ActivityProtocol"
    )
    parser.add_argument(
        "--text",
        default="Smoke test: what is the capital of France?",
        help="Message text to send",
    )
    args = parser.parse_args()

    load_dotenv(ROOT_DIR / ".env")
    result = send_activity_message(text=args.text)

    print(f"status={result.status_code}")
    print(f"conversation_id={result.conversation_id}")
    if result.response_text:
        print("bot_reply=" + result.response_text)
    else:
        print("Smoke call succeeded, but no text response was extracted.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
