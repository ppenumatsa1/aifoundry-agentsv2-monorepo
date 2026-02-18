# PB Insurance Agent (RAG)

This agent uses Azure AI Foundry project connections and an MCP tool to query Foundry IQ knowledge bases. It also includes SDK-based Azure AI Search index creation and ingestion for local documents.

## Setup

1. Create and activate a virtual environment (`python3 -m venv .venv && source .venv/bin/activate`).
2. Install dependencies:
   - `pip install -e .`
3. Copy `.env.example` to `.env` and fill values.

## Run

- Ingest documents into Azure AI Search:
  - `python scripts/ingest_documents.py`
- Ask a question:
  - `python scripts/run_agent.py "What is the deductible for the basic plan?"`
- Run batch questions:
  - `python scripts/run_batch_questions.py`
- Run evals:
  - `python scripts/run_foundry_evaluations.py`

Optional using Make:

- `make ingest`
- `make run QUESTION="What is the deductible for the basic plan?"`
- `make batch`
- `make evals`

## Notes

- Authentication uses Entra ID via `DefaultAzureCredential` only.
- Runtime mode is MCP-first; on MCP 401 auth failure it automatically falls back to direct Azure AI Search retrieval.
- Default MCP approval mode is `MCP_REQUIRE_APPROVAL=never` to avoid an extra approval round-trip per request.
- You can tune call volume and wait behavior with `MCP_MAX_APPROVAL_ROUNDS`, `RESPONSE_TIMEOUT_SECONDS`, and `RESPONSE_MAX_RETRIES`.
- Search service and RBAC are provisioned via Bicep IaC.
- Place source docs in `data/insurance-docs/` (PDF or TXT).
- For MCP auth status, reproduction, and mitigation details, see `ISSUE_KB_MCP_AUTH.md`.
