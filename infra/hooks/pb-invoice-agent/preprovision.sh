#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${AZURE_LOCATION:-}" ]]; then
  azd env set AZURE_LOCATION eastus2
fi

if [[ -z "${AZURE_RESOURCE_GROUP:-}" ]]; then
  env_name="${AZD_ENV_NAME:-aifoundry}"
  azd env set AZURE_RESOURCE_GROUP "rg-${env_name}-demo"
fi
