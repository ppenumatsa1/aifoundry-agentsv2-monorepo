#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  agents/50-pb-teams-bing-agent/scripts/kusto/run-kusto-queries.sh --query-file <path> [--app-id <guid>] [--app-insights <name> --resource-group <rg>] [--output table|json]

Examples:
  agents/50-pb-teams-bing-agent/scripts/kusto/run-kusto-queries.sh --query-file agents/50-pb-teams-bing-agent/scripts/kusto/business-events.kql --app-insights aifpv7jq3mklubce-appi --resource-group rg-fa-dev2
  agents/50-pb-teams-bing-agent/scripts/kusto/run-kusto-queries.sh --query-file agents/50-pb-teams-bing-agent/scripts/kusto/dependency-flow.kql --app-id b5d7d7c5-8bd3-4628-a667-54dfd1219337 --output json
USAGE
}

QUERY_FILE=""
APP_ID=""
APP_INSIGHTS_NAME=""
RESOURCE_GROUP=""
OUTPUT="table"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --query-file)
      QUERY_FILE="$2"
      shift 2
      ;;
    --app-id)
      APP_ID="$2"
      shift 2
      ;;
    --app-insights)
      APP_INSIGHTS_NAME="$2"
      shift 2
      ;;
    --resource-group)
      RESOURCE_GROUP="$2"
      shift 2
      ;;
    --output)
      OUTPUT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$QUERY_FILE" ]]; then
  echo "--query-file is required" >&2
  usage
  exit 1
fi

if [[ ! -f "$QUERY_FILE" ]]; then
  echo "Query file not found: $QUERY_FILE" >&2
  exit 1
fi

if [[ -z "$APP_ID" ]]; then
  if [[ -z "$APP_INSIGHTS_NAME" || -z "$RESOURCE_GROUP" ]]; then
    echo "Provide --app-id OR both --app-insights and --resource-group" >&2
    usage
    exit 1
  fi
  APP_ID=$(az monitor app-insights component show \
    -a "$APP_INSIGHTS_NAME" \
    -g "$RESOURCE_GROUP" \
    --query appId -o tsv)
fi

QUERY_TEXT=$(cat "$QUERY_FILE")

az monitor app-insights query \
  --app "$APP_ID" \
  --analytics-query "$QUERY_TEXT" \
  -o "$OUTPUT"
