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

- `AZURE_AI_PROJECT_ENDPOINT` (or `PROJECT_ENDPOINT`)
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`
- `FOUNDRY_AGENT_ID`

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

### Preferred (azd + Bicep)

Set azd env values, then provision:

- `azd env set M365_IMAGE_TAG <image-tag>`
- `azd env set MICROSOFT_APP_ID <bot-app-id>`
- `azd env set MICROSOFT_APP_PASSWORD <bot-app-secret>`
- `azd env set MICROSOFT_APP_TENANT_ID <tenant-id>`
- `azd env set MICROSOFT_APP_TYPE SingleTenant`
- `azd env set FOUNDRY_AGENT_ID pb-teams-bing-agent`
- `azd env set AZURE_AI_MODEL_DEPLOYMENT_NAME gpt-4.1-mini`
- `azd provision`

Outputs include ACA app/bot endpoint values for validation.

### Post-provision

- Enable Microsoft Teams channel on the created Bot Service resource.
- Validate messaging endpoint is `https://<aca-url>/api/messages`.
