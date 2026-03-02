# pb-teams-bing-agent

Simplified Teams agent runtime aligned with the monorepo structure (`src/`, `scripts/`, `tests/`, `pyproject.toml`, multi-stage `Dockerfile`).

Flow:

Teams → Azure Bot Service → FastAPI app (`/api/messages`) → Azure AI Foundry published agent

Provisioning note:

- Root IaC provisions Azure Bot Service and enables Microsoft Teams channel automatically.
- ACA runs with ACR image pull via system-assigned managed identity.

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
- `BOT_ENDPOINT`

Optional:

- `MANAGED_IDENTITY_CLIENT_ID` (for user-assigned MI)
- `MICROSOFT_APP_TENANT_ID`
- `MICROSOFT_APP_TYPE` (default `SingleTenant`)
- `TEAMS_APP_ID` (optional stable Teams manifest id)
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

Expected checks:

- `GET /healthz` returns `200` with `{"status":"ok"}`
- unauthenticated `POST /api/messages` returns `401`

## Infrastructure as Code (IaC)

Provision infrastructure from the repository root using azd.

Run from repo root:

```bash
az login
azd provision --preview
azd provision
```

After provisioning, use values from `.azure/<env-name>/.env` for local agent `.env` setup (for example, model deployment, Foundry endpoint, and bot app settings).

## Docker

The project keeps a multi-stage `Dockerfile` and starts with:

```bash
uvicorn teams_bing_agent.app:app --host 0.0.0.0 --port 8000
```

## RBAC setup

Assign `Azure AI User` role on the Foundry project/agent scope to:

- Your local user principal (for local development)
- ACA managed identity (for deployed runtime)

## Known-good deploy + package

From repo root:

```bash
azd provision --preview
azd provision
azd deploy
```

From `agents/50-pb-teams-bing-agent`:

```bash
# sync .env from current azd env outputs (.azure/<env>/.env)
make teams-package
```

Upload `teams/build/teams-app-package.zip` to Teams Developer Portal and validate chat E2E.
