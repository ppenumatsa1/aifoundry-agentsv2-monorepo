import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from teams_bing_agent.runtime.activityprotocol_client import (  # type: ignore[import-not-found]  # noqa: E402
    send_activity_message,
)


def main() -> None:
    load_dotenv(ROOT_DIR / ".env")
    conversation_id = f"interactive-{uuid.uuid4()}"

    print("Path B interactive mode (published Foundry ActivityProtocol)")
    print("Type a message and press Enter. Type 'exit' to quit.\n")

    while True:
        user_text = input("YOU: ").strip()
        if not user_text:
            continue
        if user_text.lower() in {"exit", "quit", "q"}:
            print("Exiting.")
            return

        result = send_activity_message(text=user_text, conversation_id=conversation_id)
        reply = result.response_text or "(no text returned)"
        print(f"BOT: {reply}\n")


if __name__ == "__main__":
    main()
