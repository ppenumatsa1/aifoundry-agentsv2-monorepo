# Provisioning (Simple Bot-First Flow)

This folder contains two simple scripts for Teams bot hosting on Azure Container Apps.

## Defaults

Both scripts are hardcoded to:

- Subscription: `4f18d577-3506-4a11-85e5-a83b14727a84`
- Resource Group: `rg-fa-dev1`
- Location: `eastus2`

Resource names are auto-generated with random suffixes.

## Step 1: Provision Bot and write `MICROSOFT_APP_*`

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

## Step 2: Provision ACR + ACA app

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
