# AI Foundry Agents v2 (Domain-Driven)

This repository demonstrates Azure AI Foundry Agents v2 using a domain-driven layout where each agent is fully self-contained.

## Goals

- Each agent owns its prompts, schemas, ingestion logic, tests, and evaluations.
- No shared runtime dependencies across agents.
- Azure infrastructure managed with azd + Bicep at the repository root.

## Structure (high level)

- `infra/` Azure infrastructure (Bicep).
- `infra/hooks/<agent>/` azd lifecycle hooks per agent (preprovision/postdeploy).
- `scripts/` Reserved for future shared infra helpers.
- `agents/<domain>/` Fully isolated agent packages.

## Agents

- `invoice-assistant`: Ingests invoice documents into Azure AI Projects vector stores. Uses vector store search RAG and returns strict JSON output via Azure OpenAI Responses API validated against a schema (`answer`, `top_documents`).

## Quick start

1. Provision infrastructure (azd):
   - `azd provision`
2. Deploy (runs agent postdeploy hook):

- `azd deploy`

2. For the invoice agent:
   - `cd agents/invoice-assistant`
   - `python -m venv .venv && source .venv/bin/activate`
   - `pip install -e .`
   - Copy `.env.example` to `.env` and fill values (auth uses `DefaultAzureCredential`).
   - Run ingestion and query:
     - `python scripts/ingest_invoices.py`
     - `python scripts/run_assistant.py "What is the total amount for invoice INV-1001?"`
   - Run batch evals:
     - `python scripts/run_batch_questions.py --questions src/invoice_assistant/evals/datasets/questions.jsonl`
     - `python scripts/run_foundry_evaluations.py --data src/invoice_assistant/evals/datasets/golden_capture.jsonl`

## More sample queries

- `python scripts/run_assistant.py "What is the vendor for invoice INV-1003?"`
- `python scripts/run_assistant.py "What is the due date for invoice INV-1004?"`
- `python scripts/run_assistant.py "List the line items on invoice INV-1002."`

## Run tests

From `agents/invoice-assistant` after ingesting invoices:

- `pytest -q`

## Notes

- This repo is intentionally designed for multi-agent growth. Add new agents under `agents/<new-domain>` with their own dependencies and runtime.
