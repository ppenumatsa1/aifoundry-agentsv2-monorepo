# Architecture

## Target system

```text
CLI/User
  -> scripts/run_agent.py
    -> runtime/run.py
      -> Azure AI Foundry agent (responses API)
        -> MCP Remote Tool Server (GitHub MCP)
      <- response text
```

## Runtime boundaries

- Inbound interface: CLI scripts.
- Tooling interface: MCP remote tool via Foundry project connection.
- Identity: `DefaultAzureCredential` for Foundry and ARM operations.

## Connection strategy

Connection resolution order:

1. `MCP_PROJECT_CONNECTION_ID` from env.
2. Local cache (`.foundry/connection.json`).
3. ARM create using `AZURE_PROJECT_RESOURCE_ID` + `MCP_PAT`.
4. Existing Foundry connection lookup by name.

## Observability

- Optional App Insights (`APP_INSIGHTS_CONNECTION_STRING`).
- Structured logs and telemetry helpers under `src/mcp_agent/core/`.
