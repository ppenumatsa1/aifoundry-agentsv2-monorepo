# Product Requirements

## Problem

Users need a secure, read-only assistant that answers from SharePoint-grounded enterprise content through Azure AI Foundry.

## Goals

- Use Foundry agent with SharePoint grounding connection.
- Enforce fail-closed startup when `SHAREPOINT_CONNECTION_ID` is invalid/missing.
- Keep runtime minimal for single question, batch capture, and evaluator flows.
- Preserve least-privilege posture for SharePoint access.
- Support optional App Insights telemetry.

## Non-goals

- No MCP tool configuration in this agent.
- No local ingestion/indexing pipeline.
- No UI surface; script-driven workflow only.

## Functional Requirements

- Resolve connection id and validate ARM resource format.
- Resolve/create Foundry agent with SharePoint tool binding.
- Execute conversation+response flow and return extracted text.
- Support batch/eval/orchestrator script paths.

## Success Criteria

- Agent run succeeds for valid SharePoint connection id.
- Invalid connection id fails fast with actionable error.
- Batch/eval scripts operate on captured datasets.
