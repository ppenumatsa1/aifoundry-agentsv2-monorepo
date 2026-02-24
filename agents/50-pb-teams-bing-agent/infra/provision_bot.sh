#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env"

SUBSCRIPTION="4f18d577-3506-4a11-85e5-a83b14727a84"
RESOURCE_GROUP="rg-fa-dev1"
BOT_LOCATION="global"

RANDOM_SUFFIX="$(printf '%s-%s-%s' "$(date +%s%N)" "$RANDOM" "$RANDOM" | sha256sum | cut -c1-6)"
BOT_NAME="agent-bot-${RANDOM_SUFFIX}"
APP_DISPLAY_NAME="${BOT_NAME}-app"
PLACEHOLDER_ENDPOINT="https://placeholder.invalid/api/messages"
APP_TYPE="SingleTenant"

upsert_env() {
  local key="$1"
  local value="$2"
  local file="$3"

  if grep -qE "^${key}=" "$file"; then
    python3 - "$key" "$value" "$file" <<'PY'
import re
import sys
k, v, f = sys.argv[1], sys.argv[2], sys.argv[3]
text = open(f, encoding='utf-8').read()
text = re.sub(rf'^{re.escape(k)}=.*$', f'{k}={v}', text, flags=re.M)
open(f, 'w', encoding='utf-8').write(text)
PY
  else
    printf '\n%s=%s\n' "$key" "$value" >> "$file"
  fi
}

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}. Copy .env.example to .env first." >&2
  exit 1
fi

az account set --subscription "${SUBSCRIPTION}"
az account show >/dev/null

TENANT_ID="$(az account show --query tenantId -o tsv)"

echo "[1/4] Creating Entra app registration"
APP_ID="$(az ad app create --display-name "${APP_DISPLAY_NAME}" --sign-in-audience AzureADMyOrg --query appId -o tsv)"
az ad sp create --id "${APP_ID}" --only-show-errors >/dev/null 2>&1 || true
APP_PASSWORD="$(az ad app credential reset --id "${APP_ID}" --append --display-name "bot-secret" --years 2 --query password -o tsv)"

echo "[2/4] Ensuring resource group"
az group create --name "${RESOURCE_GROUP}" --location eastus2 --output none

echo "[3/4] Creating Azure Bot registration"
az bot create \
  --resource-group "${RESOURCE_GROUP}" \
  --name "${BOT_NAME}" \
  --app-type "${APP_TYPE}" \
  --location "${BOT_LOCATION}" \
  --endpoint "${PLACEHOLDER_ENDPOINT}" \
  --appid "${APP_ID}" \
  --tenant-id "${TENANT_ID}" \
  --sku F0 \
  --output none

echo "[4/4] Writing bot credentials to .env"
upsert_env "MICROSOFT_APP_ID" "${APP_ID}" "${ENV_FILE}"
upsert_env "MICROSOFT_APP_PASSWORD" "${APP_PASSWORD}" "${ENV_FILE}"
upsert_env "MICROSOFT_APP_TENANT_ID" "${TENANT_ID}" "${ENV_FILE}"
upsert_env "MICROSOFT_APP_TYPE" "${APP_TYPE}" "${ENV_FILE}"

echo
echo "Bot provisioned."
echo "BOT_NAME=${BOT_NAME}"
echo "MICROSOFT_APP_ID and related values were written to ${ENV_FILE}"
echo "Next: run infra/provision_aca.sh and then update bot endpoint to ACA /api/messages URL."
