#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
ORCHESTRATOR="${ROOT_DIR}/agents/pb-insurance-agent/scripts/run_orchestrator.sh"

if [[ ! -f "${ORCHESTRATOR}" ]]; then
  echo "pb-insurance-agent orchestrator not found yet: ${ORCHESTRATOR}"
  echo "Skipping agent run for now."
  exit 0
fi

echo ""
echo "==================== PB Insurance Agent Orchestrator ===================="
echo "Running: ${ORCHESTRATOR}"
echo "Started at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "======================================================================="

bash "${ORCHESTRATOR}" 2>&1 | tee /tmp/pb-insurance-agent-orchestrator.log

echo "======================================================================="
echo "Finished at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Log file: /tmp/pb-insurance-agent-orchestrator.log"
echo "======================================================================="
