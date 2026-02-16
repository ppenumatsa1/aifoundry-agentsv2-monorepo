# MCP Agent

Lightweight Azure AI Foundry agent that connects to a remote MCP server as a tool. No ingestion, no vector stores, no JSON schema outputs.

## Setup

1. `python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -e .`
3. Copy `.env.example` to `.env` and set values.

Optional using Make:

- `make venv`
- `make install`
- `make env`

## Run

- Ask a question: `python scripts/run_agent.py "What is my username in GitHub?"`
- Run batch questions (questions.jsonl -> golden_capture.jsonl):
  - `python scripts/run_batch_questions.py --questions src/mcp_agent/evals/datasets/questions.jsonl`
- Run Foundry evaluators on captured dataset:
  - `python scripts/run_foundry_evaluations.py --data src/mcp_agent/evals/datasets/golden_capture.jsonl`
- Run the full orchestration flow:
  - `python scripts/run_orchestrator.py`

Optional using Make:

- `make run QUESTION="What is my username in GitHub?"`
- `make batch`
- `make evals`
- `make orchestrate`

## Recommended flow (Foundry v2)

1. Use `azd provision` for infra only (Foundry account, project, models, shared resources).
2. Run agents locally per repo using the steps above; each agent owns its own setup, runs, and evals.
3. Keep `.env` local per agent. Use `.azure/<env>/.env` as the source of truth and copy values as needed.

## Notes

- MCP tool configuration comes from `.env`.
- Project connections can be created via a single ARM REST call if `AZURE_PROJECT_RESOURCE_ID` is set. Otherwise, create the connection in Foundry and set `MCP_PROJECT_CONNECTION_ID` or `MCP_CONNECTION_NAME` in `.env`.
- ARM creation uses `MCP_PAT` and `MCP_SERVER_URL` with a fixed RemoteTool payload (Authorization header + 2025-10-01-preview).
- MCP approval requests are auto-approved when `MCP_AUTO_APPROVE=true`.
- Foundry evaluator runs require `AZURE_AI_MODEL_DEPLOYMENT_NAME` (judge deployment).
- To log evaluation results in Foundry, set `AZURE_AI_PROJECT_ENDPOINT` in `.env`.
- Telemetry to App Insights uses `APP_INSIGHTS_CONNECTION_STRING` and OpenTelemetry.

## Environment naming (standard)

- Use `AZURE_AI_PROJECT_ENDPOINT` and `AZURE_AI_MODEL_DEPLOYMENT_NAME` as the canonical names.
- Keep real values in `.env` only; `.env.example` should use empty placeholders.
