from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from teams_bing_agent.runtime.run import ask_with_conversation  # type: ignore[import-not-found]  # noqa: E402
from teams_bing_agent.runtime.state import ConversationStateStore  # type: ignore[import-not-found]  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Registration-free two-turn smoke test")
    parser.add_argument(
        "--q1",
        default="What is the capital of France?",
        help="First user question",
    )
    parser.add_argument(
        "--q2",
        default="And what is the weather there right now?",
        help="Second user follow-up question",
    )
    args = parser.parse_args()

    load_dotenv(ROOT_DIR / ".env")

    state_store = ConversationStateStore()
    teams_conversation_id = f"anon-smoke-{uuid.uuid4()}"

    result_1 = ask_with_conversation(
        question=args.q1,
        teams_conversation_id=teams_conversation_id,
        state_store=state_store,
    )

    result_2 = ask_with_conversation(
        question=args.q2,
        teams_conversation_id=teams_conversation_id,
        state_store=state_store,
    )

    reply1 = (result_1.response_text or "").strip()
    reply2 = (result_2.response_text or "").strip()

    if not reply1:
        raise SystemExit("Smoke test failed: empty first reply")
    if not reply2:
        raise SystemExit("Smoke test failed: empty second reply")

    print("status=200")
    print(f"conversation_id={result_1.foundry_conversation_id}")
    print("q1=" + args.q1)
    print("reply1=" + reply1)
    print("q2=" + args.q2)
    print("reply2=" + reply2)
    print("check=two-turn-conversation-ok")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
