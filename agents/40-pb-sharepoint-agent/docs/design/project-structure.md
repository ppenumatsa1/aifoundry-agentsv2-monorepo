# Project Structure

```text
agents/40-pb-sharepoint-agent/
├── README.md
├── .env.example
├── pyproject.toml
├── docs/
│   └── design/
│       ├── architecture.md
│       ├── code-flow.md
│       ├── prd.md
│       ├── project-structure.md
│       ├── tech-stack.md
│       └── user-flow.md
├── scripts/
│   ├── run_agent.py
│   ├── run_batch_questions.py
│   ├── run_foundry_evaluations.py
│   ├── run_orchestrator.py
│   └── run_orchestrator.sh
├── src/
│   └── sharepoint_agent/
│       ├── config.py
│       ├── prompt.md
│       ├── core/
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

This agent is SharePoint-grounding focused and intentionally excludes MCP and ingestion modules.
