import sys

from invoice_assistant.runtime.run import ask


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python scripts/run_agent.py "<question>"')
    question = sys.argv[1]
    response = ask(question)
    print(response.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
