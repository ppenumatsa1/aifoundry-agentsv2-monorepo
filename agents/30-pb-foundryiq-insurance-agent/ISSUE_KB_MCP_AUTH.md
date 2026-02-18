# KB MCP Status and Repro

## TL;DR

- Platform issue: Foundry Responses API MCP calls to Knowledge Base endpoint can return `401`, `400 (tool_user_error)`, downstream dependency failures (for example internal `500`), and intermittent throttling (`429`) in preview (`2025-11-01-Preview`).
- Current app behavior: **MCP-first**, then **automatic direct Search fallback**. If fallback generation is also throttled, the app returns top retrieved context excerpts instead of failing.

---

## Current Runtime Mode

1. Try MCP tool via Responses API (`tool_choice="required"`)
2. On MCP tool failures (`401`, MCP `tool_user_error` `400`, dependency `500`, and `429` throttling), fallback to direct Azure AI Search retrieval + grounded response generation
3. If fallback generation also hits `429`, return retrieved context excerpts (graceful degraded response) instead of raising an exception

This is the only supported runtime mode in this repo right now.

---

## Platform Gap Summary

Known preview behavior:

1. MCP calls through Foundry Responses API can intermittently fail with `401`, `400 (tool_user_error)` wrapping downstream MCP failures (for example dependency `500`), or `429` throttling.
2. Runtime handles these by falling back to direct Search retrieval and generation.
3. If the fallback generation call is also throttled (`429`), runtime returns retrieved excerpts as a degraded but non-failing response.

---

## Operational Validation (app behavior)

```bash
source .venv/bin/activate
make ingest
make run QUESTION="What is the deductible for the basic plan?"
```

Expected:

- MCP succeeds -> normal MCP-grounded answer
- MCP failure (`401`, MCP `400 tool_user_error`, dependency `500`, or `429`) -> log warning `mcp_tool_failed_using_fallback`, answer still returned
- If fallback generation is throttled -> log warning `fallback_generation_rate_limited`, return retrieved excerpts

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
- Search module: `infra/modules/ai-search.bicep`
- Search RBAC module: `infra/modules/rbac.bicep`
- Infra orchestration: `infra/main.bicep`

---

## Status

- **Status**: Mitigated in app (fallback + degraded mode enabled)
- **Impact**: MCP path can degrade, but user flow avoids hard failures
- **Next step**: keep tracking Foundry preview MCP/tool reliability fixes and reduce throttling impact
