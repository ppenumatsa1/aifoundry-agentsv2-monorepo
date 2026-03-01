# 50-pb-teams-bing-agent — Implementation Notes

_Last updated: 2026-03-01_

## Scope completed

Refactored to a simplified runtime aligned to other monorepo agents while removing unnecessary complexity:

- Removed MSAL connection manager wiring
- Removed custom JWT middleware configuration branches
- Removed conversation state mapping layer
- Removed dynamic Foundry agent version creation path
- Kept FastAPI + Microsoft Agents hosting entrypoint
- Kept project structure (`src`, `scripts`, `tests`, `pyproject.toml`, multi-stage `Dockerfile`)

## Current runtime flow

1. Teams/Bot posts activity to `POST /api/messages`.
2. Message handler reads incoming text.
3. Runtime calls Foundry via `azure-ai-projects` using `DefaultAzureCredential`.
4. Runtime references an already-published agent via `FOUNDRY_AGENT_ID`.
5. Response text is returned to Teams.

## Configuration model

Primary environment variables:

- `AZURE_AI_PROJECT_ENDPOINT`
- `AZURE_PROJECT_RESOURCE_ID`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`
- `FOUNDRY_AGENT_ID`
- `MICROSOFT_APP_ID`
- `MICROSOFT_APP_PASSWORD`

Optional:

- `MANAGED_IDENTITY_CLIENT_ID`
- `MICROSOFT_APP_TENANT_ID`
- `MICROSOFT_APP_TYPE`
- `FASTAPI_HOST`
- `FASTAPI_PORT`

Notes:

- `AZURE_AI_PROJECT_ENDPOINT` is the canonical endpoint input.
- No `FOUNDRY_AGENT_ENDPOINT` is used.
- No Foundry secret values are required.

## Auth/RBAC behavior

- Local development: `az login` + `DefaultAzureCredential`.
- ACA runtime: Managed Identity + `DefaultAzureCredential`.
- Foundry access is RBAC-based (`Azure AI User` assignment).
- Bearer tokens are still required on outbound Foundry calls; `DefaultAzureCredential` acquires them automatically.

## Files impacted by simplification

- `src/teams_bing_agent/app.py`
- `src/teams_bing_agent/config.py`
- `src/teams_bing_agent/runtime/run.py`
- `src/teams_bing_agent/runtime/agent.py`
- `src/teams_bing_agent/runtime/openai_client.py`
- `tests/unit/test_agent.py`

Removed:

- `src/teams_bing_agent/runtime/state.py`
- `tests/unit/test_state.py`

## Validation snapshot

Executed in `agents/50-pb-teams-bing-agent`:

- `python -m pytest -m unit -q` → passing
- App import smoke check → passing

## Remaining follow-ups (optional)

- Update any infra/deployment docs that still describe pre-refactor MSAL/JWT branches.
- Add an integration smoke test for `/api/messages` with a mocked Foundry call.
