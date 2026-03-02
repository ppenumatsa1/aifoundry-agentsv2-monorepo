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

## Simplifications applied (and why)

- Removed custom Bot adapter/auth branching and standardized on Microsoft Agents SDK defaults (`CloudAdapter`, `JwtAuthorizationMiddleware`, `MsalConnectionManager`) to reduce auth edge cases.
- Kept a single message path (`/api/messages` -> `on_message` -> Foundry call) to simplify debugging and operational tracing.
- Removed provision-time bootstrap server behavior in ACA and forced image entrypoint usage (`command: []`, `args: []`) so deploy revisions run the real app process.
- Added direct Foundry batch/eval scripts so local evaluations do not depend on FastAPI/Teams ingress availability.
- Kept canonical env naming (`AZURE_AI_PROJECT_ENDPOINT`, `AZURE_AI_MODEL_DEPLOYMENT_NAME`, `FOUNDRY_AGENT_ID`, `MICROSOFT_APP_*`) to avoid alias/normalization complexity.
- Added Teams channel provisioning in IaC to remove manual portal setup drift.
- Packaged `prompt.md` and added loader fallback to prevent runtime file-not-found failures in deployed container images.

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
- `APP_INSIGHTS_CONNECTION_STRING` (enables telemetry/tracing when set)
- `OTEL_SERVICE_NAME` (default `pb-teams-bing-agent`)
- `OTEL_SERVICE_VERSION` (default `0.1.0`)
- `OTEL_CAPTURE_MESSAGE_CONTENT` (default `false`)

## Telemetry (minimal flow)

Telemetry is intentionally light in this first iteration and is enabled only when `APP_INSIGHTS_CONNECTION_STRING` is configured.

Instrumented boundaries:

- FastAPI ingress: `/api/messages`
- Message processing: Teams activity handler -> Foundry `ask(...)`
- Foundry call: `responses.create(...)` with latency and response id
- Tool usage hint: response output item types containing `tool` or `search`

Exception handling:

- Domain errors return structured JSON (`{"error":{"code":"...","message":"..."}}`)
- Unhandled exceptions return `500` JSON with `internal_error` and are logged with stack trace

Quick App Insights checks (Logs):

Queries are versioned under [scripts/kusto](scripts/kusto):

- [scripts/kusto/business-events.kql](scripts/kusto/business-events.kql)
- [scripts/kusto/dependency-flow.kql](scripts/kusto/dependency-flow.kql)
- [scripts/kusto/exceptions.kql](scripts/kusto/exceptions.kql)
- [scripts/kusto/event-counts.kql](scripts/kusto/event-counts.kql)

Use [scripts/kusto/run-kusto-queries.sh](scripts/kusto/run-kusto-queries.sh) to execute them:

```bash
agents/50-pb-teams-bing-agent/scripts/kusto/run-kusto-queries.sh \
  --query-file agents/50-pb-teams-bing-agent/scripts/kusto/business-events.kql \
  --app-insights aifpv7jq3mklubce-appi \
  --resource-group rg-fa-dev2
```

Optional noise controls (not enabled by default):

- keep framework loggers at `WARNING` and app business events at `INFO`
- apply App Insights sampling only if telemetry volume/cost requires it

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

Canonical azd env vars for this agent:

```sh
azd env set m365AcrName            <existing-acr-name>   # optional, if reusing an existing ACR
azd env set m365BotName            <existing-bot-name>   # optional, if reusing an existing Azure Bot resource
azd env set m365AgentId            pb-teams-bing-agent
azd env set m365ModelDeploymentName gpt-4.1-mini
azd env set m365FoundryProjectEndpoint https://<foundry>.services.ai.azure.com/api/projects/<project>   # optional override
```

Optional bot credential overrides (when you do NOT want auto app-registration):

```sh
azd env set m365BotAppId           <existing-bot-app-client-id>
azd env set m365BotAppPassword     <existing-bot-app-client-secret>
azd env set m365BotTenantId        <tenant-id>
azd env set m365BotAppType         SingleTenant
```

If `m365BotAppId` is empty, the preprovision hook creates/reuses an Entra app registration, ensures a service principal, and sets `m365BotAppId`, `m365BotAppPassword`, and `m365BotTenantId` in the azd environment.

App Insights connection string is wired automatically through IaC into Container Apps (`APP_INSIGHTS_CONNECTION_STRING`).

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
