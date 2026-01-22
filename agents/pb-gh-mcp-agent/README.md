# MCP Agent

Lightweight Azure AI Foundry agent that connects to a remote MCP server as a tool. No ingestion, no vector stores, no JSON schema outputs.

## Setup

1. `python -m venv .venv && source .venv/bin/activate`
2. `pip install -e .`
3. Copy `.env.example` to `.env` and set values.

## Run

- Ask a question: `python scripts/run_agent.py "What is my username in GitHub?"`
- Run batch questions (questions.jsonl -> golden_capture.jsonl):
  - `python scripts/run_batch_questions.py --questions src/mcp_agent/evals/datasets/questions.jsonl`
- Run Foundry evaluators on captured dataset:
  - `python scripts/run_foundry_evaluations.py --data src/mcp_agent/evals/datasets/golden_capture.jsonl`
- Run the full orchestration flow:
  - `python scripts/run_orchestrator.py`

## Notes

- MCP tool configuration comes from `.env`.
- Project connections can be created via a single ARM REST call if `AZURE_PROJECT_RESOURCE_ID` is set. Otherwise, create the connection in Foundry and set `MCP_PROJECT_CONNECTION_ID` or `MCP_CONNECTION_NAME` in `.env`.
- ARM creation uses `MCP_PAT` and `MCP_SERVER_URL` with a fixed RemoteTool payload (Authorization header + 2025-10-01-preview).
- MCP approval requests are auto-approved when `MCP_AUTO_APPROVE=true`.
- Foundry evaluator runs require `AZURE_AI_MODEL_DEPLOYMENT_NAME` (judge deployment).
- To log evaluation results in Foundry, set `AZURE_AI_PROJECT_ENDPOINT` in `.env`.
- Telemetry to App Insights uses `APP_INSIGHTS_CONNECTION_STRING` and OpenTelemetry.
