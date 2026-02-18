#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ROOT_DIR}/.env"
  set +a
fi

export AZURE_AI_MODEL_DEPLOYMENT_NAME="${AZURE_AI_MODEL_DEPLOYMENT_NAME:-gpt-4.1-mini}"

if [[ -z "${SHAREPOINT_CONNECTION_ID:-}" ]]; then
  echo "SHAREPOINT_CONNECTION_ID is required. Set it in ${ROOT_DIR}/.env." >&2
  exit 1
fi

cd "${ROOT_DIR}"

if [[ ! -x ".venv/bin/python" ]]; then
  python3 -m venv .venv
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -e .
fi

.venv/bin/python "${SCRIPT_DIR}/run_orchestrator.py"
