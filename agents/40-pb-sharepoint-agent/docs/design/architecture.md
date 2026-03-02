# Architecture

## Target system

```text
CLI/User
  -> scripts/run_agent.py
    -> runtime/run.py
      -> Foundry agent (SharePoint grounding connection)
      <- response text
```

## Security model

- SharePoint-only grounding path (no MCP usage in this agent runtime).
- Fail-closed connection validation in runtime/connections module.
- Recommended least privilege: `Sites.Selected` + site-level read grant.

## Runtime boundaries

- Inbound interface: CLI scripts.
- Tool connection: `SHAREPOINT_CONNECTION_ID` (full Foundry project connection ARM id).
- Identity: `DefaultAzureCredential` for Foundry calls.

## Observability

- Structured app logs through core logging utilities.
- Optional App Insights via OpenTelemetry settings.
