#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

AZD_ENV_NAME="${AZD_ENV_NAME:-${AZD_ENV:-dev}}"
AZD_ENV_FILE="${ROOT_DIR}/../.azure/${AZD_ENV_NAME}/.env"
COPIED_ENV=0

if [[ ! -f "${ROOT_DIR}/.env" && -f "${AZD_ENV_FILE}" ]]; then
  cp "${AZD_ENV_FILE}" "${ROOT_DIR}/.env"
  COPIED_ENV=1
fi

if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ROOT_DIR}/.env"
  set +a
fi

rm -f "${ROOT_DIR}/.foundry/agent.json" "${ROOT_DIR}/.foundry/connection.json"

if [[ -z "${AZURE_AI_PROJECT_ENDPOINT:-}" && -n "${foundryName:-}" && -n "${foundryProjectName:-}" ]]; then
  export AZURE_AI_PROJECT_ENDPOINT="https://${foundryName}.services.ai.azure.com/api/projects/${foundryProjectName}"
  export AZURE_PROJECTS_ENDPOINT="${AZURE_AI_PROJECT_ENDPOINT}"
fi

if [[ -z "${AZURE_PROJECT_RESOURCE_ID:-}" && -n "${AZURE_SUBSCRIPTION_ID:-}" && -n "${AZURE_RESOURCE_GROUP:-}" && -n "${foundryName:-}" && -n "${foundryProjectName:-}" ]]; then
  export AZURE_PROJECT_RESOURCE_ID="/subscriptions/${AZURE_SUBSCRIPTION_ID}/resourceGroups/${AZURE_RESOURCE_GROUP}/providers/Microsoft.CognitiveServices/accounts/${foundryName}/projects/${foundryProjectName}"
fi

export AZURE_OPENAI_MODEL="${AZURE_OPENAI_MODEL:-gpt-5}"
export AZURE_AI_MODEL_DEPLOYMENT_NAME="${AZURE_AI_MODEL_DEPLOYMENT_NAME:-gpt-4.1-mini}"

MCP_SERVER_URL="${MCP_SERVER_URL:-https://api.githubcopilot.com/mcp}"
export MCP_SERVER_URL

if [[ -z "${MCP_PAT:-}" ]]; then
  echo "MCP_PAT is required. Set it in ${AZD_ENV_FILE} (via 'azd env set MCP_PAT=...') or enter it now." >&2
  read -r -s -p "Enter MCP_PAT (GitHub PAT): " MCP_PAT
  echo
  if [[ -z "${MCP_PAT}" ]]; then
    echo "MCP_PAT is required to continue." >&2
    exit 1
  fi
  export MCP_PAT
fi

cd "${ROOT_DIR}"

if [[ ! -x ".venv/bin/python" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    python3 -m venv .venv
  else
    python -m venv .venv
  fi
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -e .
fi

.venv/bin/python "${SCRIPT_DIR}/run_orchestrator.py"
