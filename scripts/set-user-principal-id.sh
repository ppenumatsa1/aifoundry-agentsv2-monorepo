#!/usr/bin/env sh
set -eu

if ! command -v az >/dev/null 2>&1; then
  echo "az CLI not found; skipping userPrincipalId setup"
  exit 0
fi

get_env_value() {
  key="$1"
  value="$(azd env get-value "${key}" 2>/dev/null || true)"

  case "${value}" in
    *ERROR:*)
      value=""
      ;;
  esac

  if printf '%s' "${value}" | grep -q '[\r\n]'; then
    value=""
  fi

  printf '%s' "${value}"
}

set_env_if_empty() {
  key="$1"
  value="$2"
  current="$(get_env_value "${key}")"
  if [ -z "${current}" ] && [ -n "${value}" ]; then
    azd env set "${key}" "${value}" >/dev/null
  fi
}

if ! command -v azd >/dev/null 2>&1; then
  echo "azd CLI not found; skipping userPrincipalId setup"
  exit 0
fi

user_object_id="$(az ad signed-in-user show --query id -o tsv 2>/dev/null || true)"

if [ -z "${user_object_id}" ]; then
  echo "Could not resolve signed-in user object id; skipping userPrincipalId update"
else
  azd env set USER_PRINCIPAL_ID "${user_object_id}" >/dev/null
  azd env set userPrincipalId "${user_object_id}" >/dev/null
fi

foundry_name="$(get_env_value foundryName)"
foundry_project_name="$(get_env_value foundryProjectName)"

existing_foundry_name="$(get_env_value existingFoundryName)"
existing_foundry_project_name="$(get_env_value existingFoundryProjectName)"

if [ -z "${existing_foundry_name}" ] && [ -n "${foundry_name}" ]; then
  azd env set existingFoundryName "${foundry_name}" >/dev/null
fi

if [ -z "${existing_foundry_project_name}" ] && [ -n "${foundry_project_name}" ]; then
  azd env set existingFoundryProjectName "${foundry_project_name}" >/dev/null
fi

tenant_id="$(az account show --query tenantId -o tsv 2>/dev/null || true)"

bot_app_id="$(get_env_value m365BotAppId)"
bot_app_password="$(get_env_value m365BotAppPassword)"
bot_display_name="$(get_env_value m365BotAppDisplayName)"
azd_env_name="$(get_env_value AZURE_ENV_NAME)"

if [ -z "${bot_display_name}" ]; then
  if [ -n "${azd_env_name}" ]; then
    bot_display_name="aifoundry-${azd_env_name}-teams-bot-app"
  else
    bot_display_name="aifoundry-teams-bot-app"
  fi
fi

if [ -z "${bot_app_id}" ]; then
  existing_app_id="$(az ad app list --display-name "${bot_display_name}" --query "[?displayName=='${bot_display_name}'] | [0].appId" -o tsv 2>/dev/null || true)"

  if [ -n "${existing_app_id}" ]; then
    bot_app_id="${existing_app_id}"
  else
    bot_app_id="$(az ad app create --display-name "${bot_display_name}" --sign-in-audience AzureADMyOrg --query appId -o tsv 2>/dev/null || true)"
  fi

  if [ -z "${bot_app_id}" ]; then
    echo "Failed to create or locate Entra app registration for Teams bot"
    exit 1
  fi

  azd env set m365BotAppId "${bot_app_id}" >/dev/null
fi

set_env_if_empty m365BotAppType "SingleTenant"
set_env_if_empty m365BotTenantId "${tenant_id}"

az ad sp create --id "${bot_app_id}" >/dev/null 2>&1 || true

if [ -z "${bot_app_password}" ]; then
  generated_secret="$(az ad app credential reset --id "${bot_app_id}" --append --display-name "azd-bot-secret" --years 2 --query password -o tsv 2>/dev/null || true)"

  if [ -z "${generated_secret}" ]; then
    echo "Failed to generate bot app secret for m365BotAppId=${bot_app_id}"
    exit 1
  fi

  azd env set m365BotAppPassword "${generated_secret}" >/dev/null
fi

if [ -n "${user_object_id}" ]; then
  echo "Prepared azd env (userPrincipalId + Teams bot app registration)"
else
  echo "Prepared azd env (Teams bot app registration + Foundry carry-forward)"
fi