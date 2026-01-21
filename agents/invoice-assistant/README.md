# Invoice Assistant (Agent)

This agent ingests invoice documents into Azure AI Projects vector stores, then answers questions using file_search RAG with strict JSON output validation via Azure OpenAI Responses API.

## JSON schema

Responses strictly conform to the schema in `src/invoice_assistant/schema.json` and are validated with `src/invoice_assistant/schema.py`:

- `answer`: concise direct answer
- `top_documents`: 1-5 documents with `doc_id`, `file_name`, `snippet`

## Setup

1. `python -m venv .venv && source .venv/bin/activate`
2. `pip install -e .`
3. Copy `.env.example` to `.env` and set values.

## Run

- Ingest invoices: `python scripts/ingest_invoices.py`
- Ask a question: `python scripts/run_assistant.py "What is the total amount for invoice INV-1001?"`
- Run batch questions (questions.jsonl -> golden_capture.jsonl):
  - `python scripts/run_batch_questions.py --questions src/invoice_assistant/evals/datasets/questions.jsonl`
- Run Foundry evaluators on captured dataset:
  - `python scripts/run_foundry_evaluations.py --data src/invoice_assistant/evals/datasets/golden_capture.jsonl`
- Run the full orchestration flow:
  - `python scripts/run_orchestrator.py`

## Deployment hooks

- `azd deploy` triggers the invoice assistant postdeploy hook to run `scripts/run_orchestrator.py`.
- Hook scripts live under `infra/hooks/invoice-assistant/` at the repo root.

## Example output

```json
{
  "answer": "The total amount for invoice INV-1001 is $107.42.",
  "top_documents": [
    {
      "doc_id": "turn0file0",
      "file_name": "invoice_INV-1001.txt",
      "snippet": "Invoice ID: INV-1001 ... Total Due: $107.42"
    }
  ]
}
```

## Notes

- This agent is fully self-contained and does not share runtime dependencies with other agents.
- Foundry evaluator runs require `AZURE_AI_MODEL_DEPLOYMENT_NAME` (judge deployment).
- To log evaluation results in Foundry, set `AZURE_PROJECTS_ENDPOINT` in `.env`.
- Telemetry to App Insights uses `APP_INSIGHTS_CONNECTION_STRING` and OpenTelemetry (see `.env.example`).

## Evaluation datasets

- questions.jsonl: input questions for batch runs.
- golden_capture.jsonl: captured query/response/context (and tool fields when available).

## Flow (technical)

### Ingestion

1. `scripts/ingest_invoices.py` loads settings and creates `AIProjectClient`.
2. Uses `get_openai_client()` to create a vector store and upload invoice files from `data/invoices`.
3. Saves the vector store id to `.foundry/vector_store.json` for later reuse.

### Invocation

1. `scripts/run_assistant.py` calls `runtime.run.ask()`.
2. `runtime/run.py` creates or reuses an agent with `file_search` over the vector store.
3. `runtime/run.py` calls the Responses API with the agent reference for JSON output.
4. `runtime/run.py` validates the JSON with Pydantic and returns `InvoiceAssistantResponse`.

## Flow (semantic)

### Ingestion

1. Collect invoice documents.
2. Upload them to a vector store.
3. Build a searchable index automatically during upload.

### Invocation

1. User asks a question.
2. Agent retrieves relevant snippets via file search.
3. Model answers using prompt + retrieved context via Azure OpenAI Responses API.
4. Response is validated against the JSON schema.
