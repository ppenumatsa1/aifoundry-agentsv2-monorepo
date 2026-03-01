#!/usr/bin/env sh
set -eu

if ! command -v az >/dev/null 2>&1; then
  echo "az CLI not found; skipping userPrincipalId setup"
  exit 0
fi

if ! command -v azd >/dev/null 2>&1; then
  echo "azd CLI not found; skipping userPrincipalId setup"
  exit 0
fi

user_object_id="$(az ad signed-in-user show --query id -o tsv 2>/dev/null || true)"

if [ -z "${user_object_id}" ]; then
  echo "Could not resolve signed-in user object id; userPrincipalId not updated"
  exit 0
fi

azd env set USER_PRINCIPAL_ID "${user_object_id}" >/dev/null
azd env set userPrincipalId "${user_object_id}" >/dev/null

copy_env_value() {
  source_key="$1"
  target_key="$2"
  value="$(azd env get-value "${source_key}" 2>/dev/null || true)"

  case "${value}" in
    *ERROR:*)
      value=""
      ;;
  esac

  case "${value}" in
    *$'\n'*)
      value=""
      ;;
  esac

  if [ -n "${value}" ]; then
    azd env set "${target_key}" "${value}" >/dev/null
  fi
}

copy_env_value "foundryName" "existingFoundryName"
copy_env_value "foundryProjectName" "existingFoundryProjectName"
copy_env_value "M365_ACR_NAME" "m365AcrName"
copy_env_value "M365_IMAGE_TAG" "m365ImageTag"
copy_env_value "MICROSOFT_APP_ID" "m365BotAppId"
copy_env_value "MICROSOFT_APP_PASSWORD" "m365BotAppPassword"
copy_env_value "MICROSOFT_APP_TENANT_ID" "m365BotTenantId"
copy_env_value "MICROSOFT_APP_TYPE" "m365BotAppType"
copy_env_value "FOUNDRY_AGENT_ID" "m365AgentId"
copy_env_value "AZURE_AI_MODEL_DEPLOYMENT_NAME" "m365ModelDeploymentName"
copy_env_value "AZURE_AI_PROJECT_ENDPOINT" "m365FoundryProjectEndpoint"

echo "Set azd env vars USER_PRINCIPAL_ID and userPrincipalId to ${user_object_id}"