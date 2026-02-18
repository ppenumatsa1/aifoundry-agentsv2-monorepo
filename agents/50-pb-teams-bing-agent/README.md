# pb-teams-bing-agent

Minimal Microsoft Teams bot in Python that forwards incoming Teams message activities to an Azure AI Foundry Agents v2 agent and returns the final response.

## What this project includes

- Microsoft 365 Agents SDK + FastAPI endpoint at `/api/messages`
- Message-only handler (ignores non-message activities)
- Azure AI Foundry call via `azure-ai-projects` + `DefaultAzureCredential`
- Teams conversation ID to Foundry conversation ID mapping (in-memory)
- Auto-create/reuse of a Foundry agent version with Web Search tool (preview)

This version uses Web Search tool preview for current/public web lookups.

## Required environment variables

- `AZURE_AI_PROJECT_ENDPOINT`
- `FOUNDRY_AGENT_ID`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`
- `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID`
- `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET`
- `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID`

Optional Web Search Preview tuning:

- `WEB_SEARCH_CONTEXT_SIZE` (`low` | `medium` | `high`)
- `WEB_SEARCH_COUNTRY`
- `WEB_SEARCH_REGION`
- `WEB_SEARCH_CITY`
- `WEB_SEARCH_TIMEZONE`

Optional compatibility alias supported by config:

- `PROJECT_ENDPOINT` (maps to `AZURE_AI_PROJECT_ENDPOINT`)

Optional compatibility aliases for auth (auto-mapped to `CONNECTIONS__...`):

- `MICROSOFT_APP_ID`
- `MICROSOFT_APP_PASSWORD`
- `MICROSOFT_APP_TENANT_ID`

## Quick start

```bash
make venv
make install
make env
# edit .env
make run

# optional evaluation flow
make batch
make evals
make orchestrate
```

FastAPI endpoint:

- `POST /api/messages`

## Authenticated smoke test (end-to-end)

1. Start the server in one terminal:

```bash
make run
```

2. In another terminal, run:

```bash
make smoke-auth
```

This script:

- acquires a bearer token using your bot credentials
- sends a signed message activity to `/api/messages`
- checks for successful HTTP response (and prints inline reply when available)

Required auth env values (preferred):

- `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID`
- `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET`
- `CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID`

## Anonymous smoke test (local/dev)

Use this when you want to validate the Foundry-backed bot runtime before wiring Azure Bot/Teams registration credentials.

Run:

```bash
make smoke-anon
```

This smoke test is registration-free and executes the same `ask_with_conversation` runtime path directly.

Use `make smoke-auth` when you want to validate the `/api/messages` channel endpoint with signed bearer tokens.

## Batch + evaluations

- `make batch` runs questions from `src/teams_bing_agent/evals/datasets/questions.jsonl`
- Captured outputs are written to `src/teams_bing_agent/evals/datasets/golden_capture.jsonl`
- `make evals` submits the captured dataset to Foundry evaluators and prints the report URL
- `make orchestrate` runs `smoke-anon -> batch -> evals` in one command
- `make e2e-once` is an alias of `make orchestrate`

## Message flow

1. Teams sends message activity to `/api/messages`
2. Bot extracts text + Teams conversation ID
3. Runtime resolves or creates Foundry conversation for that Teams conversation
4. Runtime ensures the Foundry agent version exists (creates it on first run if needed)
5. Runtime sends user message to Foundry agent reference
6. Bot returns agent final text back to Teams

## Notes

- Current mapping store is in-memory for MVP and resets on process restart.
- Scale-out production deployments should persist mapping in external storage (e.g., Redis/Cosmos DB).
- The app now wires `MsalConnectionManager`, `Authorization`, and `JwtAuthorizationMiddleware` for production-style Microsoft 365 Agents SDK request validation.
