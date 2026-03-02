# Project Structure

```text
agents/20-pb-mcp-gh-agent/
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
│   └── mcp_agent/
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

This agent is runtime-centric: no ingestion package, no vector store workflow, and no web service host.
