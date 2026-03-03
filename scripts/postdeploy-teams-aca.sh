#!/usr/bin/env bash
# postdeploy-teams-aca.sh
#
# Runs AFTER azd pushes the runtime Docker image to ACR.
#
# Calls aca.bicep with the freshly-pushed image name (SERVICE_TEAMSBINGAGENT_IMAGE_NAME,
# set by azd after its native push) to:
#   • Update the Container App revision to the new image
#   • Reconcile the Bot Service endpoint to the actual live ACA FQDN
#
# This runs on every deploy, so it is idempotent by design.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Capture the image azd just pushed BEFORE loading stored env (which may have
# the previous deploy's value).
PUSHED_IMAGE="${SERVICE_TEAMSBINGAGENT_IMAGE_NAME:-}"

echo "==> [postdeploy] Loading azd environment..."
eval "$(azd env get-values 2>/dev/null)"

# Prefer the live value set by azd in the current process over the stored one.
IMAGE_FULL="${PUSHED_IMAGE:-${SERVICE_TEAMSBINGAGENT_IMAGE_NAME:-}}"
: "${IMAGE_FULL:?SERVICE_TEAMSBINGAGENT_IMAGE_NAME must be set by azd deploy before postdeploy runs}"

echo "==> [postdeploy] Reconciling Container App + Bot endpoint with image:"
echo "                 ${IMAGE_FULL}"

# ── Required provision outputs ─────────────────────────────────────────────────
: "${AZURE_RESOURCE_GROUP:?AZURE_RESOURCE_GROUP must be set by azd provision}"
: "${AZURE_CONTAINER_REGISTRY_NAME:?AZURE_CONTAINER_REGISTRY_NAME must be set by azd provision}"
: "${AZURE_ACA_APP_NAME:?AZURE_ACA_APP_NAME must be set by azd provision}"
: "${AZURE_ACA_ENV_NAME:?AZURE_ACA_ENV_NAME must be set by azd provision}"
: "${AZURE_BOT_NAME:?AZURE_BOT_NAME must be set by azd provision}"
: "${AZURE_UAMI_ID:?AZURE_UAMI_ID must be set by azd provision}"
: "${AZURE_UAMI_CLIENT_ID:?AZURE_UAMI_CLIENT_ID must be set by azd provision}"
: "${AZURE_FOUNDRY_PROJECT_ENDPOINT:?AZURE_FOUNDRY_PROJECT_ENDPOINT must be set by azd provision}"
: "${AZURE_APPINSIGHTS_NAME:?AZURE_APPINSIGHTS_NAME must be set by azd provision}"

# ── Required user env vars ─────────────────────────────────────────────────────
: "${m365BotAppId:?m365BotAppId must be set  →  azd env set m365BotAppId <app-registration-client-id>}"
: "${m365BotTenantId:?m365BotTenantId must be set  →  azd env set m365BotTenantId <tenant-id>}"
: "${m365BotAppPassword:?m365BotAppPassword must be set  →  azd env set m365BotAppPassword <client-secret>}"

PARAMS_FILE="$(mktemp /tmp/aca-params-XXXX.json)"
trap 'rm -f "${PARAMS_FILE}"' EXIT

cat > "${PARAMS_FILE}" <<ENDPARAMS
{
  "\$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "location":                   { "value": "${location:-${AZURE_LOCATION:-eastus2}}" },
    "acrName":                    { "value": "${AZURE_CONTAINER_REGISTRY_NAME}" },
    "acaEnvironmentName":         { "value": "${AZURE_ACA_ENV_NAME}" },
    "acaAppName":                 { "value": "${AZURE_ACA_APP_NAME}" },
    "botName":                    { "value": "${AZURE_BOT_NAME}" },
    "uamiId":                     { "value": "${AZURE_UAMI_ID}" },
    "uamiClientId":               { "value": "${AZURE_UAMI_CLIENT_ID}" },
    "imageFullName":              { "value": "${IMAGE_FULL}" },
    "botAppId":                   { "value": "${m365BotAppId}" },
    "botTenantId":                { "value": "${m365BotTenantId}" },
    "botAppType":                 { "value": "${m365BotAppType:-SingleTenant}" },
    "botAppPassword":             { "value": "${m365BotAppPassword}" },
    "foundryProjectEndpoint":     { "value": "${AZURE_FOUNDRY_PROJECT_ENDPOINT}" },
    "foundryModelDeploymentName": { "value": "${m365ModelDeploymentName:-gpt-4.1-mini}" },
    "foundryAgentId":             { "value": "${m365AgentId:-pb-teams-bing-agent}" },
    "appInsightsName":            { "value": "${AZURE_APPINSIGHTS_NAME}" }
  }
}
ENDPARAMS

echo "==> [postdeploy] Applying aca.bicep..."
az deployment group create \
    --resource-group "${AZURE_RESOURCE_GROUP}" \
    --name "aca-deploy" \
    --template-file "${PROJECT_ROOT}/infra/modules/aca.bicep" \
    --parameters "@${PARAMS_FILE}"

echo "==> [postdeploy] Done."
echo "                 Container App is running: ${IMAGE_FULL}"

# Print the live bot endpoint for easy verification.
BOT_ENDPOINT=$(az deployment group show \
    --resource-group "${AZURE_RESOURCE_GROUP}" \
    --name "aca-deploy" \
    --query "properties.outputs.botEndpoint.value" \
    --output tsv 2>/dev/null || echo "(endpoint lookup failed)")
echo "                 Bot endpoint: ${BOT_ENDPOINT}"
