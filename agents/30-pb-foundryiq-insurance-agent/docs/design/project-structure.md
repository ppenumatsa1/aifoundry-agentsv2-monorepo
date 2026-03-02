# Project Structure

```text
agents/30-pb-foundryiq-insurance-agent/
├── README.md
├── ISSUE_KB_MCP_AUTH.md
├── .env.example
├── pyproject.toml
├── data/
│   └── insurance-docs/
├── docs/
│   └── design/
│       ├── architecture.md
│       ├── code-flow.md
│       ├── prd.md
│       ├── project-structure.md
│       ├── tech-stack.md
│       └── user-flow.md
├── scripts/
│   ├── ingest_documents.py
│   ├── run_agent.py
│   ├── run_batch_questions.py
│   ├── run_foundry_evaluations.py
│   ├── run_orchestrator.py
│   └── run_orchestrator.sh
├── src/
│   └── insurance_agent/
│       ├── config.py
│       ├── prompt.md
│       ├── core/
│       ├── ingest/
│       │   ├── index.py
│       │   └── loaders.py
│       ├── evals/
│       │   ├── batch.py
│       │   └── datasets/
│       └── runtime/
│           ├── agent.py
│           ├── cache.py
│           ├── connections.py
│           ├── openai_client.py
│           └── run.py
└── tests/
    ├── integration/
    └── unit/
```

This agent combines ingestion + runtime + fallback logic in one self-contained package.
