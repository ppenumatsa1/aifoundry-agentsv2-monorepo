# Product Requirements

## Problem

Users need a lightweight agent that can answer GitHub-related questions by invoking a remote MCP server tool from Azure AI Foundry.

## Goals

- Run a Foundry agent that uses an MCP remote tool connection.
- Keep runtime simple (CLI-first) with no ingestion or vector-store dependencies.
- Support single question flow, batch capture, and Foundry evaluator runs.
- Support ARM-based project connection creation when `AZURE_PROJECT_RESOURCE_ID` is available.
- Emit optional App Insights telemetry through OpenTelemetry settings.

## Non-goals

- No custom web UI.
- No local document indexing or RAG vector store pipeline.
- No multi-agent orchestration beyond script-level orchestration.

## Functional Requirements

- Resolve/create Foundry agent with MCP tool binding.
- Create/reuse conversation and invoke responses API.
- Handle MCP approval requests with auto-approve option.
- Return extracted text response and metadata for eval capture.

## Success Criteria

- `scripts/run_agent.py` returns valid response text.
- Batch/eval scripts produce and evaluate `golden_capture.jsonl`.
- MCP connection resolves reliably via explicit id, cached id, ARM creation, or Foundry lookup.
