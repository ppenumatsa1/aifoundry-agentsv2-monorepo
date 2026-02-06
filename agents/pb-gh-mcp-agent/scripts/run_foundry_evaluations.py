# ruff: noqa: I001

import argparse
import json
import os
from pathlib import Path
import sys
import time

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from dotenv import load_dotenv  # noqa: E402
from mcp_agent.core.logging import get_logger  # type: ignore[import-not-found]  # noqa: E402
from mcp_agent.evals.batch import build_project_client  # type: ignore[import-not-found]  # noqa: E402

DEFAULT_DATA_PATH = ROOT_DIR / "src/mcp_agent/evals/datasets/golden_capture.jsonl"


def load_eval_items(data_path: Path) -> list[dict]:
    items: list[dict] = []
    for line in data_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        items.append(row)
    return items


def load_judge_model_config() -> dict:
    load_dotenv(dotenv_path=ROOT_DIR / ".env")
    deployment = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME")

    if not deployment:
        raise SystemExit("AZURE_AI_MODEL_DEPLOYMENT_NAME is required.")

    return {
        "deployment_name": deployment,
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Azure AI Evaluation SDK agent evaluators on the generated dataset."
    )
    parser.add_argument(
        "--data",
        default=str(DEFAULT_DATA_PATH),
        help="Path to golden_capture.jsonl",
    )
    parser.add_argument(
        "--evaluation-name",
        default="mcp-agent-eval",
        help="Evaluation run name.",
    )
    parser.add_argument(
        "--no-log-to-foundry",
        action="store_true",
        help="Skip logging results to the Foundry project.",
    )
    return parser


def main() -> None:
    logger = get_logger(__name__)
    args = build_arg_parser().parse_args()
    data_path = Path(args.data)

    if not data_path.exists():
        raise SystemExit(f"Evaluation data not found: {data_path}")

    items = load_eval_items(data_path)
    if not items:
        raise SystemExit("No evaluation items found in the dataset.")

    project_client = build_project_client()
    judge_model_config = load_judge_model_config()

    logger.info(
        "running_evaluators data=%s evaluation_name=%s item_count=%s",
        str(data_path),
        args.evaluation_name,
        len(items),
    )

    data_source_config = {
        "type": "custom",
        "item_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "response": {"type": "string"},
                "context": {"type": "string"},
                "ground_truth": {"type": "string"},
            },
            "required": ["query", "response"],
        },
        "include_sample_schema": True,
    }
    initialization_parameters = judge_model_config
    testing_criteria = [
        {
            "type": "azure_ai_evaluator",
            "name": "coherence",
            "evaluator_name": "builtin.coherence",
            "initialization_parameters": initialization_parameters,
            "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}"},
        },
        {
            "type": "azure_ai_evaluator",
            "name": "fluency",
            "evaluator_name": "builtin.fluency",
            "initialization_parameters": initialization_parameters,
            "data_mapping": {"response": "{{item.response}}"},
        },
        {
            "type": "azure_ai_evaluator",
            "name": "relevance",
            "evaluator_name": "builtin.relevance",
            "initialization_parameters": initialization_parameters,
            "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}"},
        },
        {
            "type": "azure_ai_evaluator",
            "name": "groundedness",
            "evaluator_name": "builtin.groundedness",
            "initialization_parameters": initialization_parameters,
            "data_mapping": {
                "query": "{{item.query}}",
                "response": "{{item.response}}",
                "context": "{{item.context}}",
            },
        },
        {
            "type": "azure_ai_evaluator",
            "name": "retrieval",
            "evaluator_name": "builtin.retrieval",
            "initialization_parameters": initialization_parameters,
            "data_mapping": {"query": "{{item.query}}", "context": "{{item.context}}"},
        },
        {
            "type": "azure_ai_evaluator",
            "name": "intent_resolution",
            "evaluator_name": "builtin.intent_resolution",
            "initialization_parameters": initialization_parameters,
            "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}"},
        },
        {
            "type": "azure_ai_evaluator",
            "name": "task_adherence",
            "evaluator_name": "builtin.task_adherence",
            "initialization_parameters": initialization_parameters,
            "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}"},
        },
        {
            "type": "azure_ai_evaluator",
            "name": "tool_call_accuracy",
            "evaluator_name": "builtin.tool_call_accuracy",
            "initialization_parameters": initialization_parameters,
            "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}"},
        },
    ]

    with project_client.get_openai_client() as openai_client:
        eval_object = openai_client.evals.create(
            name=args.evaluation_name,
            data_source_config=data_source_config,
            testing_criteria=testing_criteria,
        )

        data_source = {
            "type": "jsonl",
            "source": {
                "type": "file_content",
                "content": [{"item": item} for item in items],
            },
        }

        response_eval_run = openai_client.evals.runs.create(
            eval_id=eval_object.id,
            name=f"Evaluation Run for {args.evaluation_name}",
            data_source=data_source,
        )

        while response_eval_run.status not in ["completed", "failed"]:
            time.sleep(5)
            response_eval_run = openai_client.evals.runs.retrieve(
                run_id=response_eval_run.id, eval_id=eval_object.id
            )

        if response_eval_run.status == "completed":
            print("✓ Evaluation run completed successfully")
            print(f"Eval Run Report URL: {response_eval_run.report_url}")
        else:
            details = response_eval_run.model_dump()
            print("Evaluation run failed.")
            print(details)


if __name__ == "__main__":
    main()
