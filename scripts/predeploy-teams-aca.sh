#!/usr/bin/env bash
# predeploy-teams-aca.sh
#
# Runs BEFORE azd builds and pushes the Docker image.
#
# First deploy: ACA doesn't exist yet — build an init image via ACR remote build,
#               then create the Container App via aca.bicep using the UAMI that was
#               pre-provisioned with AcrPull + Foundry AI User roles.
#
# Subsequent deploys: ACA already exists — skip immediately so azd's native
#                     containerapp update handles the image refresh.
#
# After azd pushes the real image, postdeploy-teams-aca.sh reconciles the
# Container App config and updates the Bot Service endpoint.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "==> [predeploy] Loading azd environment..."
eval "$(azd env get-values 2>/dev/null)"

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

echo "==> [predeploy] Checking if Container App '${AZURE_ACA_APP_NAME}' exists..."
if az containerapp show \
    --resource-group "${AZURE_RESOURCE_GROUP}" \
    --name "${AZURE_ACA_APP_NAME}" \
    --output none 2>/dev/null; then
  echo "==> [predeploy] Container App already exists — skipping init."
  echo "                azd will update the image; postdeploy will reconcile the bot endpoint."
  exit 0
fi

echo "==> [predeploy] Container App not found — building init image..."

INIT_TAG="init-$(date +%Y%m%d%H%M%S)"
az acr build \
    --registry "${AZURE_CONTAINER_REGISTRY_NAME}" \
    --image "pb-teams-bing-agent:${INIT_TAG}" \
    "${PROJECT_ROOT}/agents/50-pb-teams-bing-agent"

INIT_IMAGE="${AZURE_CONTAINER_REGISTRY_NAME}.azurecr.io/pb-teams-bing-agent:${INIT_TAG}"
echo "==> [predeploy] Init image pushed: ${INIT_IMAGE}"

echo "==> [predeploy] Waiting briefly for ACA environment stabilization..."
sleep 15

echo "==> [predeploy] Waiting for ACA environment '${AZURE_ACA_ENV_NAME}' to report Succeeded..."
for _ in $(seq 1 12); do
  ace_state="$(az containerapp env show \
    --resource-group "${AZURE_RESOURCE_GROUP}" \
    --name "${AZURE_ACA_ENV_NAME}" \
    --query "properties.provisioningState" -o tsv 2>/dev/null || true)"

  if [ "${ace_state}" = "Succeeded" ]; then
    break
  fi
  sleep 5
done

# ── Deploy aca.bicep with the init image ───────────────────────────────────────
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
    "imageFullName":              { "value": "${INIT_IMAGE}" },
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

echo "==> [predeploy] Creating Container App via aca.bicep..."
if ! az deployment group create \
  --resource-group "${AZURE_RESOURCE_GROUP}" \
  --name "aca-deploy" \
  --template-file "${PROJECT_ROOT}/infra/modules/aca.bicep" \
  --parameters "@${PARAMS_FILE}"; then
  echo "==> [predeploy] First ACA deployment attempt failed; retrying once after 15s..."
  sleep 15
  az deployment group create \
    --resource-group "${AZURE_RESOURCE_GROUP}" \
    --name "aca-deploy" \
    --template-file "${PROJECT_ROOT}/infra/modules/aca.bicep" \
    --parameters "@${PARAMS_FILE}"
fi

echo "==> [predeploy] Container App created successfully."
echo "                azd will now build and push the real runtime image."
