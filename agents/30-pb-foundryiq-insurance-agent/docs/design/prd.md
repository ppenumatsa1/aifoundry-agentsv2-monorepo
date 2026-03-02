# Product Requirements

## Problem

Insurance support scenarios need grounded answers from enterprise knowledge with robust fallback behavior when MCP tool calls fail.

## Goals

- Ingest insurance documents into Azure AI Search index.
- Use Foundry agent with Foundry IQ MCP knowledge tool as primary retrieval path.
- Auto-fallback to direct Azure AI Search retrieval + synthesis on MCP failures/timeouts.
- Support batch capture and Foundry evaluator runs.
- Keep authentication Entra-based (`DefaultAzureCredential`) and telemetry optional.

## Non-goals

- No UI surface in this sample.
- No cross-agent shared runtime coupling.

## Functional Requirements

- Build/update search index and knowledge source/base via ingest script.
- Resolve/create Foundry agent and invoke with tool-required behavior.
- Handle MCP approval rounds with configurable limits.
- Detect MCP tool auth/user errors and fallback to direct search answering.

## Success Criteria

- `scripts/ingest_documents.py` populates search index successfully.
- `scripts/run_agent.py` returns useful answers in both MCP and fallback paths.
- Batch/eval scripts complete with captured dataset and evaluator run.
