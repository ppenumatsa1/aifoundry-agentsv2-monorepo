# SharePoint Agent (Foundry Agents v2)

Minimal Azure AI Foundry agent that uses a SharePoint grounding tool for **docs-read-only** responses.

## Security posture

- SharePoint-only mode (no MCP tools).
- Fail-closed startup if `SHAREPOINT_CONNECTION_ID` is missing or invalid.
- Read-only grounding intent.
- Recommend least privilege: `Sites.Selected` + site-level **Read** grant.

## Setup

1. `python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -e .`
3. `cp .env.example .env`
4. Edit `.env` and set:
   - `AZURE_AI_PROJECT_ENDPOINT`
   - `AZURE_AI_MODEL_DEPLOYMENT_NAME`
   - `SHAREPOINT_CONNECTION_ID` (full Foundry project connection ARM ID)

Optional with Make:

- `make venv`
- `make install`
- `make env`

## Run

- Single question:
  - `python scripts/run_agent.py "Summarize key security requirements from the connected SharePoint docs."`
- Batch capture:
  - `python scripts/run_batch_questions.py --questions src/sharepoint_agent/evals/datasets/questions.jsonl`
- Foundry evaluators:
  - `python scripts/run_foundry_evaluations.py --data src/sharepoint_agent/evals/datasets/golden_capture.jsonl`
- Full orchestration:
  - `python scripts/run_orchestrator.py`

## SharePoint connection requirements

Use a Foundry project connection ID similar to:

`/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.MachineLearningServices/workspaces/<ws>/connections/<name>`

The agent validates this format and exits if it is invalid.

## Secure configuration checklist

- Use a dedicated SharePoint site/library for this agent.
- Grant read-only access to the app registration.
- Avoid tenant-wide permissions where possible.
- Keep secrets in `.env` only (never commit).
- For shared/prod environments, move secrets to Key Vault and managed identities.

## Notes

- `AZURE_PROJECT_RESOURCE_ID` is optional for this sample and kept for cross-project consistency.
- Telemetry is optional via `APP_INSIGHTS_CONNECTION_STRING`.
