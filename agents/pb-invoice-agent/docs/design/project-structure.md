# Project Structure

This agent is self-contained under `agents/pb-invoice-agent` with its own dependencies, prompts, schemas, scripts, tests, and evals.

Key modules:

- `src/invoice_assistant/core/`: shared utilities (paths, logging, exceptions, schema/prompt loaders).
- `src/invoice_assistant/core/telemetry.py`: OpenTelemetry + Azure Monitor setup.
- `src/invoice_assistant/runtime/`: orchestration, agent creation, caching, schema loading.
- `src/invoice_assistant/ingest/`: vector store creation, upload, and cache handling.
- `scripts/`: thin CLI wrappers around runtime/ingest modules plus orchestrator.
- `data/invoices/`: sample invoice documents for ingestion.
- `src/invoice_assistant/prompt.md`: agent instructions template.
- `src/invoice_assistant/schema.json`: strict JSON response schema.
- `.foundry/`: local caches (vector store id, agent id).
- `src/invoice_assistant/evals/datasets/`: evaluation datasets (questions and captured runs).

## Full structure (important files)

```
.
├── README.md
├── .env.example
├── .env
├── .gitignore
├── pyproject.toml
├── data/
│   └── invoices/
│       ├── invoice_INV-1001.txt
│       ├── invoice_INV-1002.txt
│       ├── invoice_INV-1003.txt
│       ├── invoice_INV-1004.txt
│       └── invoice_INV-1005.txt
├── docs/
│   └── design/
│       ├── architecture.md
│       ├── prd.md
│       ├── project-structure.md
│       ├── tech-stack.md
│       └── user-flow.md
├── scripts/
│   ├── ingest_invoices.py
│   ├── run_agent.py
│   ├── run_batch_questions.py
│   └── run_foundry_evaluations.py
│   └── run_orchestrator.py
├── src/
│   └── invoice_assistant/
│       ├── __init__.py
│       ├── config.py
│       ├── prompt.md
│       ├── schema.json
│       ├── schema.py
│       ├── core/
│       │   ├── exceptions.py
│       │   ├── logging.py
│       │   ├── telemetry.py
│       │   ├── paths.py
│       │   ├── prompt_loader.py
│       │   └── schema_loader.py
│       ├── ingest/
│       │   ├── cache.py
│       │   ├── index.py
│       │   └── upload.py
│       ├── runtime/
│       │   ├── agent.py
│       │   ├── cache.py
│       │   ├── messages.py
│       │   ├── openai_client.py
│       │   └── run.py
│       └── evals/
│           ├── batch.py
│           └── datasets/
│               ├── questions.jsonl
│               └── golden_capture.jsonl
├── tests/
│   ├── integration/
│   │   └── test_runtime.py
│   └── unit/
│       └── test_schema.py
└── .foundry/
	├── agent.json
	└── vector_store.json
```

Local-only directories like `.venv/` and `.pytest_cache/` are excluded.
