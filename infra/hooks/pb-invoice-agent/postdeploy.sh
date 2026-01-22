#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
ORCHESTRATOR="${ROOT_DIR}/agents/pb-invoice-agent/scripts/run_orchestrator.sh"

echo ""
echo "==================== Invoice Assistant Orchestrator ===================="
echo "Running: ${ORCHESTRATOR}"
echo "Started at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "======================================================================="

bash "${ORCHESTRATOR}" 2>&1 | tee /tmp/pb-invoice-agent-orchestrator.log

echo "======================================================================="
echo "Finished at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Log file: /tmp/pb-invoice-agent-orchestrator.log"
echo "======================================================================="
