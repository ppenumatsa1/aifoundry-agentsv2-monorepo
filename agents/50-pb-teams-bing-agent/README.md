# pb-teams-bing-agent

Production-ready skeleton for Microsoft Teams with a single path:

Teams -> Azure Bot Service -> ACA-hosted M365 SDK app -> Azure AI Foundry Agent.

## Architecture

- Bot App Registration identity handles Teams/Bot authentication only.
- Azure Container Apps Managed Identity handles Foundry authorization only.
- No On-Behalf-Of flow.
- No Foundry client secret in runtime.

## Required environment variables

### Bot identity (Azure Bot Service)

- `MICROSOFT_APP_ID`
- `MICROSOFT_APP_PASSWORD`
- `MICROSOFT_APP_TENANT_ID`
- `MICROSOFT_APP_TYPE` (default: `SingleTenant`)

### Foundry runtime

- `FOUNDRY_AGENT_ENDPOINT`

Optional:

- `USE_MANAGED_IDENTITY=true` (force MI locally if needed)
- `MANAGED_IDENTITY_CLIENT_ID` (for user-assigned MI)

### Local host

- `FASTAPI_HOST` (default: `0.0.0.0`)
- `FASTAPI_PORT` (default: `8000`)

### Foundry agent creation settings

- `AZURE_AI_PROJECT_ENDPOINT`
- `FOUNDRY_AGENT_ID` (default: `pb-teams-bing-agent`)

## Quick start

```bash
make venv
make install
make env
# edit .env
make run
```

Messaging endpoint:

- `POST /api/messages`

## Commands

- `make run` start M365 bot server
- `make batch` scaffold entrypoint (not implemented yet)
- `make evals` scaffold entrypoint (not implemented yet)
- `make orchestrate` scaffold entrypoint (not implemented yet)
- `make create-agent` create/print Foundry agent from runtime module
- `make test` run unit tests

## Security model

- Teams auth token is validated by M365 Agents SDK middleware.
- Foundry token is obtained by backend credential flow:
  - ACA runtime: `ManagedIdentityCredential`
  - Local dev: `DefaultAzureCredential` (CLI/user sign-in)

## Azure setup notes

- Create Azure Bot Service registration.
- Enable Microsoft Teams channel.
- Set messaging endpoint to `https://<aca-url>/api/messages`.
- Enable System Assigned Managed Identity on ACA.
- Grant ACA MI `AI User` role at Foundry project scope.
