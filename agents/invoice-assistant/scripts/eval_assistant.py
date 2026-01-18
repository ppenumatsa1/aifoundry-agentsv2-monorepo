from pathlib import Path

from invoice_assistant.evals.runner import run_evals


def main() -> None:
    results = run_evals(Path("src/invoice_assistant/evals/datasets/goldens.jsonl"))
    for row in results:
        print(row)


if __name__ == "__main__":
    main()
