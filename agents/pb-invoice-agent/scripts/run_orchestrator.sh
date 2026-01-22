#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

if [[ -x ".venv/bin/python" ]]; then
  .venv/bin/python "${SCRIPT_DIR}/run_orchestrator.py"
else
  python "${SCRIPT_DIR}/run_orchestrator.py"
fi
