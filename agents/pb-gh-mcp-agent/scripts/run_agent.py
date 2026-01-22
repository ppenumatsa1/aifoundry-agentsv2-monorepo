from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from mcp_agent.runtime.run import ask  # type: ignore[import-not-found]  # noqa: E402


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python scripts/run_agent.py "<question>"')
    question = sys.argv[1]
    response_text = ask(question)
    print(response_text)


if __name__ == "__main__":
    main()
