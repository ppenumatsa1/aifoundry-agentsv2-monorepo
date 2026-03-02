# User Flow

1. Operator places source files in `data/insurance-docs/`.
2. Operator runs `scripts/ingest_documents.py` to build/update index + knowledge resources.
3. User asks a question using `scripts/run_agent.py`.
4. Runtime invokes Foundry agent with MCP knowledge tool required.
5. If MCP flow succeeds, grounded answer is returned.
6. If MCP tool fails (401/tool error/timeout), runtime falls back to direct Search retrieval + model synthesis.
7. Optional: run batch capture and evaluator scripts for quality tracking.
