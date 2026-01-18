# Product Requirements

## Problem

Users need accurate invoice data extraction and question answering over ingested invoice documents.

## Goals

- Ingest invoices into Azure AI Projects vector stores.
- Answer questions with file_search RAG via the agent.
- Return strict JSON output via Azure OpenAI Responses API and validate it by schema (`schema.json`).
- Reuse vector store and agent via local cache for faster runs.

## Non-goals

- No shared runtime dependencies between agents.
- No UI; CLI-only for now.
