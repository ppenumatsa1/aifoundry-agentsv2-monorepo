#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
AGENT_NAME="${AGENT_NAME:-${AZD_AGENT:-pb-invoice-agent}}"

case "${AGENT_NAME}" in
  pb-gh-mcp-agent)
    bash "${ROOT_DIR}/infra/hooks/pb-gh-mcp-agent/preprovision.sh"
    ;;
  pb-invoice-agent)
    bash "${ROOT_DIR}/infra/hooks/pb-invoice-agent/preprovision.sh"
    ;;
  *)
    echo "Unknown AGENT_NAME: ${AGENT_NAME}" >&2
    exit 1
    ;;
esac
