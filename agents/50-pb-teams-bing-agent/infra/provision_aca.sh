#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env"

SUBSCRIPTION="4f18d577-3506-4a11-85e5-a83b14727a84"
RESOURCE_GROUP="rg-fa-dev1"
LOCATION="eastus2"
FOUNDRY_SCOPE="/subscriptions/4f18d577-3506-4a11-85e5-a83b14727a84/resourceGroups/rg-fa-dev1"
LOG_ANALYTICS_WORKSPACE_RESOURCE_ID="/subscriptions/4f18d577-3506-4a11-85e5-a83b14727a84/resourcegroups/rg-fa-dev1/providers/microsoft.operationalinsights/workspaces/aifqeip6vxgcu74m-law"

RANDOM_SUFFIX="$(printf '%s-%s-%s' "$(date +%s%N)" "$RANDOM" "$RANDOM" | sha256sum | cut -c1-6)"
ACR_NAME="teamsbingagent${RANDOM_SUFFIX}"
ACA_ENV_NAME="teamsbingagentace-${RANDOM_SUFFIX}"
ACA_APP_NAME="teamsbingagentapp-${RANDOM_SUFFIX}"
IMAGE_REPO="pb-teams-bing-agent"
IMAGE_TAG="$(date +%Y%m%d%H%M%S)"
CPU="0.5"
MEMORY="1.0Gi"

is_placeholder() {
  local value="$1"
  [[ -z "${value}" || "${value}" == "<set-me>" || "${value}" == "<placeholder>" || "${value}" == "<"*">" ]]
}

get_env_value() {
  local key="$1"
  grep -E "^${key}=" "${ENV_FILE}" | tail -1 | cut -d= -f2- || true
}

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}. Copy .env.example to .env and set values first." >&2
  exit 1
fi

MICROSOFT_APP_ID="$(get_env_value "MICROSOFT_APP_ID")"
MICROSOFT_APP_PASSWORD="$(get_env_value "MICROSOFT_APP_PASSWORD")"
MICROSOFT_APP_TENANT_ID="$(get_env_value "MICROSOFT_APP_TENANT_ID")"
MICROSOFT_APP_TYPE="$(get_env_value "MICROSOFT_APP_TYPE")"
AZURE_AI_PROJECT_ENDPOINT="$(get_env_value "AZURE_AI_PROJECT_ENDPOINT")"
if [[ -z "${AZURE_AI_PROJECT_ENDPOINT}" ]]; then
  AZURE_AI_PROJECT_ENDPOINT="$(get_env_value "PROJECT_ENDPOINT")"
fi
AZURE_AI_MODEL_DEPLOYMENT_NAME="$(get_env_value "AZURE_AI_MODEL_DEPLOYMENT_NAME")"
FOUNDRY_AGENT_ID="$(get_env_value "FOUNDRY_AGENT_ID")"

for key in MICROSOFT_APP_ID MICROSOFT_APP_PASSWORD MICROSOFT_APP_TENANT_ID AZURE_AI_PROJECT_ENDPOINT AZURE_AI_MODEL_DEPLOYMENT_NAME FOUNDRY_AGENT_ID; do
  if is_placeholder "${!key}"; then
    echo "Missing or placeholder value for ${key} in ${ENV_FILE}" >&2
    echo "Run infra/provision_bot.sh for bot creds and ensure Foundry runtime values are set in .env." >&2
    exit 1
  fi
done

if [[ -z "${MICROSOFT_APP_TYPE}" ]]; then
  MICROSOFT_APP_TYPE="MultiTenant"
fi

az account set --subscription "${SUBSCRIPTION}"
az account show >/dev/null
az extension add --name containerapp --upgrade --only-show-errors >/dev/null

echo "[1/7] Ensuring resource group: ${RESOURCE_GROUP}"
az group create --name "${RESOURCE_GROUP}" --location "${LOCATION}" --output none

echo "[2/7] Ensuring ACR: ${ACR_NAME}"
az acr create \
  --name "${ACR_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --location "${LOCATION}" \
  --sku Basic \
  --admin-enabled true \
  --output none

ACR_LOGIN_SERVER="$(az acr show --name "${ACR_NAME}" --resource-group "${RESOURCE_GROUP}" --query loginServer -o tsv)"
ACR_ID="$(az acr show --name "${ACR_NAME}" --resource-group "${RESOURCE_GROUP}" --query id -o tsv)"
ACR_USERNAME="$(az acr credential show --name "${ACR_NAME}" --resource-group "${RESOURCE_GROUP}" --query username -o tsv)"
ACR_PASSWORD="$(az acr credential show --name "${ACR_NAME}" --resource-group "${RESOURCE_GROUP}" --query passwords[0].value -o tsv)"
IMAGE_REF="${ACR_LOGIN_SERVER}/${IMAGE_REPO}:${IMAGE_TAG}"
LOG_ANALYTICS_WORKSPACE_NAME="${LOG_ANALYTICS_WORKSPACE_RESOURCE_ID##*/}"
LOG_ANALYTICS_WORKSPACE_RG="$(printf '%s' "${LOG_ANALYTICS_WORKSPACE_RESOURCE_ID}" | sed -n 's|.*/resourcegroups/\([^/]*\)/providers/.*|\1|p')"
LOG_ANALYTICS_WORKSPACE_ID="$(az monitor log-analytics workspace show --resource-group "${LOG_ANALYTICS_WORKSPACE_RG}" --workspace-name "${LOG_ANALYTICS_WORKSPACE_NAME}" --query customerId -o tsv)"
LOG_ANALYTICS_WORKSPACE_KEY="$(az monitor log-analytics workspace get-shared-keys --resource-group "${LOG_ANALYTICS_WORKSPACE_RG}" --workspace-name "${LOG_ANALYTICS_WORKSPACE_NAME}" --query primarySharedKey -o tsv)"

echo "[3/7] Building and pushing image to ACR: ${IMAGE_REF}"
az acr build \
  --registry "${ACR_NAME}" \
  --image "${IMAGE_REPO}:${IMAGE_TAG}" \
  "${PROJECT_ROOT}" \
  --output none

echo "[4/7] Ensuring ACA environment: ${ACA_ENV_NAME}"
az containerapp env create \
  --name "${ACA_ENV_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --location "${LOCATION}" \
  --logs-workspace-id "${LOG_ANALYTICS_WORKSPACE_ID}" \
  --logs-workspace-key "${LOG_ANALYTICS_WORKSPACE_KEY}" \
  --output none

echo "[5/7] Creating ACA app: ${ACA_APP_NAME}"
az containerapp create \
  --name "${ACA_APP_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --environment "${ACA_ENV_NAME}" \
  --image "${IMAGE_REF}" \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 1 \
  --cpu "${CPU}" \
  --memory "${MEMORY}" \
  --system-assigned \
  --registry-server "${ACR_LOGIN_SERVER}" \
  --registry-username "${ACR_USERNAME}" \
  --registry-password "${ACR_PASSWORD}" \
  --secrets "ms-app-password=${MICROSOFT_APP_PASSWORD}" \
  --env-vars \
    MICROSOFT_APP_ID="${MICROSOFT_APP_ID}" \
    MICROSOFT_APP_TENANT_ID="${MICROSOFT_APP_TENANT_ID}" \
    MICROSOFT_APP_TYPE="${MICROSOFT_APP_TYPE}" \
    AZURE_AI_PROJECT_ENDPOINT="${AZURE_AI_PROJECT_ENDPOINT}" \
    AZURE_AI_MODEL_DEPLOYMENT_NAME="${AZURE_AI_MODEL_DEPLOYMENT_NAME}" \
    FOUNDRY_AGENT_ID="${FOUNDRY_AGENT_ID}" \
    MICROSOFT_APP_PASSWORD="secretref:ms-app-password" \
  --output none

APP_PRINCIPAL_ID="$(az containerapp show --name "${ACA_APP_NAME}" --resource-group "${RESOURCE_GROUP}" --query identity.principalId -o tsv)"

echo "[6/7] Ensuring AcrPull assignment for ACA managed identity"
az role assignment create \
  --assignee-object-id "${APP_PRINCIPAL_ID}" \
  --assignee-principal-type ServicePrincipal \
  --scope "${ACR_ID}" \
  --role AcrPull \
  --output none 2>/dev/null || true

echo "[7/7] Foundry RBAC assignment"
az role assignment create \
  --assignee-object-id "${APP_PRINCIPAL_ID}" \
  --assignee-principal-type ServicePrincipal \
  --scope "${FOUNDRY_SCOPE}" \
  --role "Azure AI User" \
  --output none 2>/dev/null || true

APP_FQDN="$(az containerapp show --name "${ACA_APP_NAME}" --resource-group "${RESOURCE_GROUP}" --query properties.configuration.ingress.fqdn -o tsv)"

echo
echo "Provisioning complete."
echo "Container image: ${IMAGE_REF}"
echo "ACA app URL: https://${APP_FQDN}"
echo "Bot messaging endpoint: https://${APP_FQDN}/api/messages"
