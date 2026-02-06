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
- Place source docs in `data/insurance-docs/` (PDF or TXT).
