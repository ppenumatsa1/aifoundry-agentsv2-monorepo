#!/usr/bin/env bash
set -euo pipefail

if [[ -f ".env" ]]; then
  set -a
  source .env
  set +a
fi

require_var() {
  local var_name="$1"
  if [[ -z "${!var_name:-}" ]]; then
    echo "❌ Missing required variable: ${var_name}" >&2
    exit 1
  fi
}

if [[ -z "${AZURE_SUBSCRIPTION_ID:-}" && -n "${AZURE_PROJECT_RESOURCE_ID:-}" ]]; then
  AZURE_SUBSCRIPTION_ID="$(sed -n 's|^/subscriptions/\([^/]*\)/.*|\1|p' <<<"${AZURE_PROJECT_RESOURCE_ID}")"
fi

if [[ -z "${AZURE_RESOURCE_GROUP:-}" && -n "${AZURE_PROJECT_RESOURCE_ID:-}" ]]; then
  AZURE_RESOURCE_GROUP="$(sed -n 's|^/subscriptions/[^/]*/resourceGroups/\([^/]*\)/.*|\1|p' <<<"${AZURE_PROJECT_RESOURCE_ID}")"
fi

if [[ -z "${SEARCH_SERVICE_NAME:-}" && -n "${SEARCH_ENDPOINT:-}" ]]; then
  SEARCH_SERVICE_NAME="$(sed -n 's|^https://\([^./]*\)\.search\.windows\.net/?$|\1|p' <<<"${SEARCH_ENDPOINT}")"
fi

AZURE_LOCATION="eastus2"
SEARCH_SERVICE_SKU="free"

require_var AZURE_SUBSCRIPTION_ID
require_var AZURE_RESOURCE_GROUP
require_var AZURE_PROJECT_RESOURCE_ID
require_var SEARCH_SERVICE_NAME

echo "ℹ️ Using subscription: ${AZURE_SUBSCRIPTION_ID}"
echo "ℹ️ Resource group: ${AZURE_RESOURCE_GROUP}"
echo "ℹ️ Search service: ${SEARCH_SERVICE_NAME}"
echo "ℹ️ Location: ${AZURE_LOCATION}"
echo "ℹ️ SKU: ${SEARCH_SERVICE_SKU}"

az account show >/dev/null
az account set --subscription "${AZURE_SUBSCRIPTION_ID}"

if az search service show --resource-group "${AZURE_RESOURCE_GROUP}" --name "${SEARCH_SERVICE_NAME}" >/dev/null 2>&1; then
  existing_sku="$(az search service show --resource-group "${AZURE_RESOURCE_GROUP}" --name "${SEARCH_SERVICE_NAME}" --query sku.name -o tsv | tr '[:upper:]' '[:lower:]')"
  existing_location="$(az search service show --resource-group "${AZURE_RESOURCE_GROUP}" --name "${SEARCH_SERVICE_NAME}" --query location -o tsv | tr '[:upper:]' '[:lower:]' | tr -d ' ')"

  if [[ "${existing_sku}" != "${SEARCH_SERVICE_SKU}" || "${existing_location}" != "${AZURE_LOCATION}" ]]; then
    echo "⚠️ Existing service is sku=${existing_sku}, location=${existing_location}; recreating as sku=${SEARCH_SERVICE_SKU}, location=${AZURE_LOCATION}"
    az search service delete \
      --resource-group "${AZURE_RESOURCE_GROUP}" \
      --name "${SEARCH_SERVICE_NAME}" \
      --yes >/dev/null
    echo "🔧 Deleted existing Search service"
  else
    echo "✅ Search service already exists with required sku/location"
  fi
fi

if ! az search service show --resource-group "${AZURE_RESOURCE_GROUP}" --name "${SEARCH_SERVICE_NAME}" >/dev/null 2>&1; then
  echo "🔧 Creating Search service"
  az search service create \
    --resource-group "${AZURE_RESOURCE_GROUP}" \
    --name "${SEARCH_SERVICE_NAME}" \
    --location "${AZURE_LOCATION}" \
    --sku "${SEARCH_SERVICE_SKU}" >/dev/null
fi

SEARCH_RESOURCE_ID="$(az search service show --resource-group "${AZURE_RESOURCE_GROUP}" --name "${SEARCH_SERVICE_NAME}" --query id -o tsv)"

echo "🔧 Enforcing roles-only auth (disable local auth)"
az rest \
  --method patch \
  --uri "https://management.azure.com${SEARCH_RESOURCE_ID}?api-version=2025-05-01" \
  --body '{"properties":{"disableLocalAuth":true,"authOptions":null}}' >/dev/null

SEARCH_ENDPOINT="https://${SEARCH_SERVICE_NAME}.search.windows.net"
PROJECT_PRINCIPAL_ID="$(az resource show --ids "${AZURE_PROJECT_RESOURCE_ID}" --query identity.principalId -o tsv)"
CURRENT_USER_OBJECT_ID="$(az ad signed-in-user show --query id -o tsv 2>/dev/null || true)"

if [[ -z "${PROJECT_PRINCIPAL_ID}" ]]; then
  echo "❌ Could not resolve project managed identity principalId from AZURE_PROJECT_RESOURCE_ID" >&2
  exit 1
fi

echo "🔧 Assigning Search RBAC roles to Foundry project managed identity"
for role in "Search Service Contributor" "Search Index Data Contributor" "Search Index Data Reader"; do
  existing_assignment="$(az role assignment list \
    --assignee-object-id "${PROJECT_PRINCIPAL_ID}" \
    --scope "${SEARCH_RESOURCE_ID}" \
    --role "${role}" \
    --query "[0].id" -o tsv)"

  if [[ -n "${existing_assignment}" ]]; then
    echo "✅ Role already assigned: ${role}"
  else
    az role assignment create \
      --assignee-object-id "${PROJECT_PRINCIPAL_ID}" \
      --assignee-principal-type ServicePrincipal \
      --role "${role}" \
      --scope "${SEARCH_RESOURCE_ID}" >/dev/null
    echo "✅ Assigned role: ${role}"
  fi
done

if [[ -n "${CURRENT_USER_OBJECT_ID}" ]]; then
  echo "🔧 Assigning Search RBAC roles to signed-in user identity"
  for role in "Search Service Contributor" "Search Index Data Contributor" "Search Index Data Reader"; do
    existing_assignment="$(az role assignment list \
      --assignee-object-id "${CURRENT_USER_OBJECT_ID}" \
      --scope "${SEARCH_RESOURCE_ID}" \
      --role "${role}" \
      --query "[0].id" -o tsv)"

    if [[ -n "${existing_assignment}" ]]; then
      echo "✅ User role already assigned: ${role}"
    else
      az role assignment create \
        --assignee-object-id "${CURRENT_USER_OBJECT_ID}" \
        --assignee-principal-type User \
        --role "${role}" \
        --scope "${SEARCH_RESOURCE_ID}" >/dev/null
      echo "✅ Assigned user role: ${role}"
    fi
  done
else
  echo "⚠️ Could not resolve signed-in user object id; skipped user role assignment"
fi

echo
echo "✅ Azure AI Search RBAC setup complete"
echo "Update your .env with:"
echo "  SEARCH_ENDPOINT=${SEARCH_ENDPOINT}"
echo "  SEARCH_SERVICE_NAME=${SEARCH_SERVICE_NAME}"
echo "  AZURE_SUBSCRIPTION_ID=${AZURE_SUBSCRIPTION_ID}"
echo "  AZURE_RESOURCE_GROUP=${AZURE_RESOURCE_GROUP}"
echo "  AZURE_LOCATION=${AZURE_LOCATION}"
