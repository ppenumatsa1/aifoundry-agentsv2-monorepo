# KB MCP Status and Repro

## TL;DR

- Platform issue: Foundry Responses API MCP calls to Knowledge Base endpoint can return `401` (`tool_user_error`) in preview (`2025-11-01-Preview`).
- Current app behavior: **MCP-first**, then **automatic direct Search fallback** so `make run` still returns an answer.

---

## Current Runtime Mode

1. Try MCP tool via Responses API (`tool_choice="required"`)
2. On MCP auth `401`, fallback to direct Azure AI Search retrieval + grounded response generation

This is the only supported runtime mode in this repo right now.

---

## Quick Reproduction (platform issue)

Use `reproduce_auth_issue.py` to show the platform gap:

1. Direct MCP call with API key works ✅
2. Project connection lookup works ✅
3. Responses API MCP call fails with 401 ❌

Run:

```bash
source .venv/bin/activate
python reproduce_auth_issue.py
```

---

## Operational Validation (app behavior)

```bash
source .venv/bin/activate
make search-recreate
make ingest
make run QUESTION="What is the deductible for the basic plan?"
```

Expected:

- MCP succeeds -> normal MCP-grounded answer
- MCP 401 -> log warning `mcp_auth_failed_using_fallback`, answer still returned

---

## Required Environment

- `SEARCH_ENDPOINT`
- `KNOWLEDGE_BASE_NAME`
- `AZURE_AI_PROJECT_ENDPOINT`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`
- `MCP_PROJECT_CONNECTION_ID` (recommended)

---

## Code Pointers

- Runtime MCP + fallback: `src/insurance_agent/runtime/run.py`
- MCP tool creation (pinned connection): `src/insurance_agent/runtime/agent.py`
- Connection setup: `src/insurance_agent/runtime/connections.py`
- Search/RBAC setup script: `scripts/recreate_search_rbac.sh`

---

## Status

- **Status**: Mitigated in app (fallback enabled)
- **Impact**: MCP path degraded; user flow works
- **Next step**: keep tracking Foundry preview MCP auth fix
