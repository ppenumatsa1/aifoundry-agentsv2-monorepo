import sys

from insurance_agent.runtime.run import ask


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python scripts/run_agent.py "<question>"')
    question = sys.argv[1]
    response = ask(question)
    print(response)


if __name__ == "__main__":
    main()
