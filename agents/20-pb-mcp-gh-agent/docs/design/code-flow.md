# Code Flow

## End-to-end ASCII diagram

```text
+-------------------+      +--------------------------+      +-----------------------------+
| CLI user          | ---> | scripts/run_agent.py     | ---> | runtime/run.py::ask_*       |
| (question)        |      |                          |      |                             |
+-------------------+      +--------------------------+      +--------------+--------------+
                                                                         |
                                                                         v
                                                          +------------------------------+
                                                          | ensure_project_connection()  |
                                                          | (env/cache/ARM/lookup)      |
                                                          +--------------+---------------+
                                                                         |
                                                                         v
                                                          +------------------------------+
                                                          | Foundry responses.create     |
                                                          | (agent_reference + MCP tool) |
                                                          +--------------+---------------+
                                                                         |
                                                                         v
+-------------------+      +--------------------------+      +-----------------------------+
| CLI output        | <--- | response extraction      | <--- | MCP approval loop (optional)|
+-------------------+      +--------------------------+      +-----------------------------+
```

## Ask flow

```text
scripts/run_agent.py
  -> runtime/run.py::ask_with_metadata()
    -> build_project_client()
    -> ensure_project_connection()
    -> get_or_create_agent()
    -> openai_client.conversations.create()
    -> openai_client.responses.create(... agent_reference ...)
    -> MCP approval loop (optional)
    -> _extract_response_text()
```

## Batch/eval flow

```text
scripts/run_batch_questions.py
  -> evals/batch.py (question file -> capture file)

scripts/run_foundry_evaluations.py
  -> Foundry evaluator run on captured dataset

scripts/run_orchestrator.py
  -> run agent/batch/evals in sequence
```

## Important modules

- `src/mcp_agent/runtime/run.py`: primary runtime logic and approval loop.
- `src/mcp_agent/runtime/connections.py`: connection creation/lookup/cache.
- `src/mcp_agent/runtime/agent.py`: Foundry agent creation/reuse.
- `src/mcp_agent/evals/batch.py`: batch capture helper.
