# 50-pb-teams-bing-agent — Implementation Notes

_Last updated: 2026-02-18_

## Scope completed

Implemented a **minimal** Microsoft Teams chatbot project that forwards Teams message activities to an Azure AI Foundry Agents v2 agent and returns the agent response.

Key goals completed:

- FastAPI endpoint for agent activities
- Microsoft 365 Agents SDK integration
- Azure AI Foundry runtime call using `azure-ai-projects` + `DefaultAzureCredential`
- Teams conversation to Foundry conversation mapping (in-memory)
- Minimal local run and unit-test setup

## Project structure created

```text
agents/50-pb-teams-bing-agent/
  .env.example
  .gitignore
  Makefile
  pyproject.toml
  README.md
  IMPLEMENTATION_NOTES.md
  scripts/
    run_agent.py
  src/
    teams_bing_agent/
      __init__.py
      app.py
      config.py
      runtime/
        __init__.py
        openai_client.py
        run.py
        state.py
  tests/
    unit/
      test_runtime.py
      test_state.py
```

## What each file does

- `src/teams_bing_agent/app.py`
  - Hosts FastAPI app
  - Exposes `POST /api/messages`
  - Registers only `message` activity handler
  - For each message:
    1. Read user text + Teams conversation id
    2. Call Foundry runtime
    3. Send assistant text back

- `src/teams_bing_agent/runtime/run.py`
  - Core orchestration for Foundry call
  - Reuses existing Foundry conversation when mapped
  - Creates a new Foundry conversation on first message
  - Calls `responses.create(..., extra_body={"agent": {"name": FOUNDRY_AGENT_ID, "type": "agent_reference"}})`
  - Extracts text from response payload

- `src/teams_bing_agent/runtime/state.py`
  - Thread-safe in-memory map:
    - `teams_conversation_id -> foundry_conversation_id`

- `src/teams_bing_agent/runtime/openai_client.py`
  - Builds `AIProjectClient` with `DefaultAzureCredential`

- `src/teams_bing_agent/config.py`
  - Loads env values via `pydantic-settings`
  - Supports both:
    - `AZURE_AI_PROJECT_ENDPOINT` (canonical)
    - `PROJECT_ENDPOINT` (compat alias)

- `scripts/run_agent.py`
  - Starts app with uvicorn using config host/port

- `tests/unit/*`
  - Validates response text extraction and state mapping behavior

## Environment configuration changes

### Created and populated

- `agents/50-pb-teams-bing-agent/.env`

### Copied from reference env

Source: `agents/30-pb-foundryiq-insurance-agent/.env`

- `AZURE_AI_PROJECT_ENDPOINT`
- `PROJECT_ENDPOINT` (same value added as compatibility alias)

### Set for this agent

- `FOUNDRY_AGENT_ID=pb-foundryiq-insurance-agent` (starter value; replace with your Bing-grounded target agent id as needed)

### Kept as placeholders (must be set for Teams channel traffic)

- `MICROSOFT_APP_ID`
- `MICROSOFT_APP_PASSWORD`
- `MICROSOFT_APP_TENANT_ID`
- `MICROSOFT_APP_TYPE` defaulted to `MultiTenant`

## Dependency choices

Added minimal dependencies needed for this implementation:

- `azure-ai-projects==2.0.0b3`
- `azure-identity`
- `fastapi`
- `uvicorn`
- `microsoft-agents-activity`
- `microsoft-agents-authentication-msal`
- `microsoft-agents-hosting-core`
- `microsoft-agents-hosting-fastapi`
- `openai`
- `pydantic`, `pydantic-settings`, `python-dotenv`, `pytest`
- `aiohttp` (required transitively by agents hosting connector imports)

## Validation performed

Commands executed in `agents/50-pb-teams-bing-agent`:

- `make venv`
- `make install`
- `make test`

Result:

- Unit tests passed: **3 passed**

Additional runtime checks:

- App booted successfully with `make run`
- `GET /healthz` returns `200`
- `POST /api/messages` without bearer token returns `401` with `{"error":"Authorization header not found"}`

## Auth hardening status (updated)

Completed production-style Microsoft 365 Agents SDK auth wiring:

- `MsalConnectionManager` initialized from env-derived SDK config
- `CloudAdapter(connection_manager=...)`
- `Authorization(storage, connection_manager, ...)` attached to `AgentApplication`
- `JwtAuthorizationMiddleware` enabled on mounted `/api` sub-application
- `agent_configuration` set from `connection_manager.get_default_connection_configuration()`

Environment compatibility behavior:

- Preferred keys: `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID|CLIENTSECRET|TENANTID`
- Back-compat aliases: `MICROSOFT_APP_ID|PASSWORD|TENANT_ID` auto-map to the preferred keys at startup

## Documentation check outcome (M365 Agents SDK)

Based on Microsoft Learn pages reviewed during implementation:

- The M365 Agents SDK abstracts most Bot Framework coding concerns.
- Teams deployment still requires channel/app configuration steps (messaging endpoint, manifest/channel setup) for production use.

## Current limitations (intentional MVP)

- In-memory conversation mapping (lost on process restart)
- No persistent storage (Redis/Cosmos/etc.) yet
- No integration/e2e tests yet
- No orchestrator/batch/evals scripts in this minimal version

## Recommended next steps

1. Replace `FOUNDRY_AGENT_ID` with the intended Bing-grounded Foundry agent id.
2. Persist conversation mapping externally for scale/restart safety.
3. Add a smoke/integration test for `/api/messages` request flow.
4. Add deployment notes for Azure hosting + Teams manifest packaging.

## Quick run reminder

```bash
cd agents/50-pb-teams-bing-agent
make venv
make install
cp .env.example .env   # or keep existing .env and edit values
make run
```

Endpoint:

- `POST /api/messages`
