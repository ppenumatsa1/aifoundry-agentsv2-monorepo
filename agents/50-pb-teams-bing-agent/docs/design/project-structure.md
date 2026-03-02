# Project Structure

This agent is self-contained under `agents/50-pb-teams-bing-agent` with its own runtime, scripts, tests, Teams package assets, and design docs.

## Key modules

- `src/teams_bing_agent/app.py`: FastAPI host + Bot message endpoint and activity handler.
- `src/teams_bing_agent/config.py`: env-backed settings.
- `src/teams_bing_agent/runtime/`: Foundry client creation, agent resolution, and ask flow.
- `src/teams_bing_agent/core/`: logging, exceptions, telemetry, prompt loading.
- `scripts/`: run helpers for local run, batch capture, evaluations, orchestrator.
- `scripts/kusto/`: KQL query files + query runner for App Insights checks.
- `teams/`: Teams app manifest/template and package builder.
- `tests/`: unit and integration tests.

## Important structure (agent scope)

```text
agents/50-pb-teams-bing-agent/
├── README.md
├── .env.example
├── Dockerfile
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
│   ├── run_orchestrator.sh
│   └── kusto/
│       ├── run-kusto-queries.sh
│       ├── business-events.kql
│       ├── dependency-flow.kql
│       ├── event-counts.kql
│       └── exceptions.kql
├── src/
│   └── teams_bing_agent/
│       ├── app.py
│       ├── config.py
│       ├── prompt.md
│       ├── core/
│       │   ├── exceptions.py
│       │   ├── logging.py
│       │   ├── telemetry.py
│       │   ├── paths.py
│       │   └── prompt_loader.py
│       ├── runtime/
│       │   ├── agent.py
│       │   ├── cache.py
│       │   ├── openai_client.py
│       │   └── run.py
│       └── evals/
│           ├── batch.py
│           └── datasets/
│               ├── questions.jsonl
│               └── golden_capture.jsonl
├── teams/
│   ├── build_teams_package.py
│   ├── manifest.template.json
│   └── README.md
└── tests/
    ├── integration/
    └── unit/
```

## Infra linkage

Root infra in `infra/` provisions ACA, Bot Service (+ Teams channel), monitoring, and supporting resources. Agent runtime config is injected through IaC env/secrets.
