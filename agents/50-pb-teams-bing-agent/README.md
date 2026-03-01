# pb-teams-bing-agent

Simplified Teams agent runtime aligned with the monorepo structure (`src/`, `scripts/`, `tests/`, `pyproject.toml`, multi-stage `Dockerfile`).

Flow:

Teams → Azure Bot Service → FastAPI app (`/api/messages`) → Azure AI Foundry published agent

Authentication/authorization:

- Inbound Teams/Bot messages handled by Microsoft Agents SDK hosting components.
- Outbound Foundry access uses `DefaultAzureCredential` and RBAC (`Azure AI User`).
- Local development: `az login`.
- ACA runtime: Managed Identity.
- No Foundry API keys or client secrets required.

## Environment variables

Required:

- `AZURE_AI_PROJECT_ENDPOINT`
- `AZURE_PROJECT_RESOURCE_ID`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`
- `FOUNDRY_AGENT_ID`
- `MICROSOFT_APP_ID`
- `MICROSOFT_APP_PASSWORD`

Optional:

- `MANAGED_IDENTITY_CLIENT_ID` (for user-assigned MI)
- `MICROSOFT_APP_TENANT_ID`
- `MICROSOFT_APP_TYPE` (default `SingleTenant`)
- `FASTAPI_HOST` (default `0.0.0.0`)
- `FASTAPI_PORT` (default `8000`)

## Quick start

```bash
make venv
make install
cp .env.example .env
# set env values
az login
make run
```

Endpoints:

- `POST /api/messages`
- `GET /healthz`

## Docker

The project keeps a multi-stage `Dockerfile` and starts with:

```bash
uvicorn teams_bing_agent.app:app --host 0.0.0.0 --port 8000
```

## RBAC setup

Assign `Azure AI User` role on the Foundry project/agent scope to:

- Your local user principal (for local development)
- ACA managed identity (for deployed runtime)
