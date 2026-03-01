# Provisioning

This agent now supports provisioning via root azd + Bicep.

## Preferred path (azd + Bicep)

From repo root:

```bash
azd env set M365_IMAGE_TAG <image-tag>
azd env set MICROSOFT_APP_ID <bot-app-id>
azd env set MICROSOFT_APP_PASSWORD <bot-app-secret>
azd env set MICROSOFT_APP_TENANT_ID <tenant-id>
azd env set MICROSOFT_APP_TYPE SingleTenant
azd env set FOUNDRY_AGENT_ID pb-teams-bing-agent
azd env set AZURE_AI_MODEL_DEPLOYMENT_NAME gpt-4.1-mini
azd provision
```

The M365 module provisions:

- Azure Container Registry (ACR)
- Azure Container Apps Environment (ACE) bound to Log Analytics Workspace
- Azure Container App (ACA) with Managed Identity and runtime env vars
- Azure Bot Service registration
- Required RBAC assignments (`AcrPull`, `Azure AI User`)

## Legacy temporary scripts

The shell scripts in this folder are retained as temporary fallback helpers and can be removed once Bicep rollout is finalized.

## Script defaults

Both scripts are hardcoded to:

- Subscription: `4f18d577-3506-4a11-85e5-a83b14727a84`
- Resource Group: `rg-fa-dev1`
- Location: `eastus2`

Resource names are auto-generated with random suffixes.

## Script step 1: Provision Bot and write `MICROSOFT_APP_*`

```bash
make provision-bot
```

This runs `infra/provision_bot.sh`, which:

- Creates an Entra app registration and secret
- Creates an Azure Bot registration
- Writes these values into project `.env`:
  - `MICROSOFT_APP_ID`
  - `MICROSOFT_APP_PASSWORD`
  - `MICROSOFT_APP_TENANT_ID`
  - `MICROSOFT_APP_TYPE`

## Script step 2: Provision ACR + ACA app

```bash
make provision-aca
```

This runs `infra/provision_aca.sh`, which:

- Validates `.env` contains non-placeholder bot values and Foundry runtime values:
  - `AZURE_AI_PROJECT_ENDPOINT` (or `PROJECT_ENDPOINT`)
  - `AZURE_AI_MODEL_DEPLOYMENT_NAME`
  - `FOUNDRY_AGENT_ID`
- Builds/pushes image to ACR
- Creates ACA environment and app
- Configures app secrets and env vars
- Assigns managed identity permissions (`AcrPull`, `Azure AI User`)
- Prints the final bot messaging endpoint: `https://<fqdn>/api/messages`

## After ACA is up

Update the Azure Bot endpoint to the printed ACA URL (`/api/messages`).

## Prerequisites

- Azure CLI logged in (`az login`)
- Permissions to create app registrations and Azure resources in the target subscription/resource group
