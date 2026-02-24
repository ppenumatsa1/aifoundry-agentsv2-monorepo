# pb-teams-bing-agent

Path B runtime for Microsoft Teams integration testing: call the **published Azure AI Foundry ActivityProtocol endpoint directly** (no local FastAPI hop).

## What this project includes

- Direct ActivityProtocol caller for published Foundry application
- One-turn and two-turn smoke tests against published endpoint
- Batch question runner and Foundry evaluation flow
- Interactive CLI chat mode using one conversation id per session

## Required environment variables

- `AZURE_AI_PROJECT_ENDPOINT`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`
- `FOUNDRY_PUBLISHED_ACTIVITY_ENDPOINT`

Optional:

- `FOUNDRY_AGENT_ID` (kept for compatibility with eval tooling metadata)
- `FOUNDRY_AI_ACCESS_TOKEN` (if set, skips `az account get-access-token`)
- `FOUNDRY_PUBLISHED_APP_ID` (used as activity recipient id; defaults to `pb-teams-bing-agent`)
- Web Search tuning (`WEB_SEARCH_CONTEXT_SIZE`, `WEB_SEARCH_COUNTRY`, etc.)

## Prerequisites

- Python 3.10+
- Azure CLI authenticated (`az login`)
- Access to invoke the published application endpoint

## Quick start

```bash
make venv
make install
make env
# edit .env
make smoke-anon
```

## Commands

- `make run` interactive Path B chat client
- `make smoke-auth` one-turn published-endpoint smoke test
- `make smoke-anon` two-turn published-endpoint smoke test
- `make batch` run question dataset and capture outputs
- `make evals` submit captured dataset to Foundry evaluators
- `make orchestrate` run `smoke-anon -> batch -> evals`
- `make e2e-once` alias for `make orchestrate`

## Message flow (Path B)

1. Client (smoke/batch/interactive) creates an Activity payload.
2. Script acquires Entra token for `https://ai.azure.com` (unless `FOUNDRY_AI_ACCESS_TOKEN` is supplied).
3. Script posts activity directly to `FOUNDRY_PUBLISHED_ACTIVITY_ENDPOINT`.
4. Published Foundry application routes to the configured agent.
5. Response activities are parsed and saved/printed.

## Tie this to Teams (Path B)

Use Azure Bot Service + Teams channel to route Teams messages to the published Foundry endpoint directly.

1. In Azure Bot Service, enable **Microsoft Teams** channel.
2. Set bot messaging endpoint to:
   - `FOUNDRY_PUBLISHED_ACTIVITY_ENDPOINT`
3. Build and sideload a Teams app package using files under `teams/`.

Detailed step-by-step guide and manifest template:

- `teams/README.md`
- `teams/manifest.template.json`

## Notes

- This mode intentionally bypasses local FastAPI runtime.
- For Teams -> custom runtime path (Path A), keep a separate branch or reintroduce `/api/messages` hosting.
