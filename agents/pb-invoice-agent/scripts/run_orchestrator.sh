#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Ensure local imports resolve.
export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"

# Load environment variables if present.
if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ROOT_DIR}/.env"
  set +a
fi

# Defaults for local runs.
export AZURE_AI_MODEL_DEPLOYMENT_NAME="${AZURE_AI_MODEL_DEPLOYMENT_NAME:-gpt-4.1-mini}"
export AZURE_OPENAI_API_VERSION="${AZURE_OPENAI_API_VERSION:-2024-05-01-preview}"

# Agent-specific configuration.
export INVOICE_DATASET_NAME="${INVOICE_DATASET_NAME:-invoices-dataset}"
export INVOICE_VECTORSTORE_NAME="${INVOICE_VECTORSTORE_NAME:-invoices-vectorstore}"
export INVOICE_AGENT_NAME="${INVOICE_AGENT_NAME:-invoice-assistant}"
export INVOICE_TOP_K="${INVOICE_TOP_K:-5}"

cd "${ROOT_DIR}"

# Bootstrap venv if needed.
if [[ ! -x ".venv/bin/python" ]]; then
  python3 -m venv .venv
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -e .
fi

# Run the orchestrator.
.venv/bin/python "${SCRIPT_DIR}/run_orchestrator.py"
