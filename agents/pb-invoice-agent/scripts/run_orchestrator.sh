#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"

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

if [[ "${COPIED_ENV}" -eq 1 ]]; then
  rm -f "${ROOT_DIR}/.foundry/agent.json" "${ROOT_DIR}/.foundry/vector_store.json"
fi

if [[ -z "${AZURE_PROJECTS_ENDPOINT:-}" && -n "${foundryName:-}" && -n "${foundryProjectName:-}" ]]; then
  export AZURE_PROJECTS_ENDPOINT="https://${foundryName}.services.ai.azure.com/api/projects/${foundryProjectName}"
fi

if [[ -z "${AZURE_OPENAI_ENDPOINT:-}" && -n "${foundryName:-}" ]]; then
  export AZURE_OPENAI_ENDPOINT="https://${foundryName}.cognitiveservices.azure.com"
fi

export AZURE_OPENAI_MODEL="${AZURE_OPENAI_MODEL:-gpt-4.1-mini}"
export AZURE_OPENAI_API_VERSION="${AZURE_OPENAI_API_VERSION:-2024-05-01-preview}"
export AZURE_AI_MODEL_DEPLOYMENT_NAME="${AZURE_AI_MODEL_DEPLOYMENT_NAME:-gpt-4.1-mini}"

export INVOICE_DATASET_NAME="${INVOICE_DATASET_NAME:-invoices-dataset}"
export INVOICE_VECTORSTORE_NAME="${INVOICE_VECTORSTORE_NAME:-invoices-vectorstore}"
export INVOICE_AGENT_NAME="${INVOICE_AGENT_NAME:-invoice-assistant}"
export INVOICE_TOP_K="${INVOICE_TOP_K:-5}"

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
