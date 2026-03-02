# Architecture

## Target system

```text
CLI/User
  -> scripts/ingest_documents.py (indexing path)
  -> scripts/run_agent.py (runtime path)
     -> Foundry agent + MCP knowledge tool (primary)
     -> Azure AI Search direct retrieval fallback (secondary)
```

## Primary path (MCP-first)

- Foundry agent is configured with MCP knowledge tool connection.
- Responses API is called with `tool_choice='required'`.
- Approval loop runs with configurable max rounds.

## Fallback path

When MCP tool invocation fails (auth/tool user error/timeout/rate limit), runtime:

- queries Azure AI Search directly,
- builds grounded context prompt,
- generates answer with OpenAI response call.

## Identity and security

- `DefaultAzureCredential` for Foundry and Search.
- Connection and server settings from `.env`.
- No static Foundry API keys required.

## Observability

- Structured logs from core logging utilities.
- Optional App Insights telemetry via OpenTelemetry settings.
