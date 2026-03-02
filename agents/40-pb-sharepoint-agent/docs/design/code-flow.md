# Code Flow

## End-to-end ASCII diagram

```text
+-------------------+      +--------------------------+      +------------------------------+
| CLI user          | ---> | scripts/run_agent.py     | ---> | runtime/run.py::ask_*        |
| (question)        |      |                          |      |                              |
+-------------------+      +--------------------------+      +--------------+---------------+
                                                                         |
                                                                         v
                                                          +-------------------------------+
                                                          | ensure_project_connection()   |
                                                          | validate SHAREPOINT_CONNECTION |
                                                          +--------------+----------------+
                                                                         |
                                                                         v
                                                          +-------------------------------+
                                                          | Foundry responses.create      |
                                                          | (SharePoint-grounded agent)   |
                                                          +--------------+----------------+
                                                                         |
                                                                         v
+-------------------+      +--------------------------+      +------------------------------+
| CLI output        | <--- | _extract_response_text() | <--- | assistant response payload   |
+-------------------+      +--------------------------+      +------------------------------+
```

## Ask flow

```text
scripts/run_agent.py
  -> runtime/run.py::ask_with_metadata()
    -> build_project_client()
    -> ensure_project_connection(settings)
       -> validate SHAREPOINT_CONNECTION_ID format
       -> cache connection id
    -> get_or_create_agent(... sharepoint connection ...)
    -> openai_client.conversations.create()
    -> openai_client.responses.create(... agent_reference ...)
    -> _extract_response_text()
```

## Batch/eval flow

```text
scripts/run_batch_questions.py
  -> evals/batch.py (questions -> golden capture)

scripts/run_foundry_evaluations.py
  -> evaluator run over captured dataset

scripts/run_orchestrator.py
  -> end-to-end scripted sequence
```

## Important modules

- `src/sharepoint_agent/runtime/run.py`: conversation/response flow.
- `src/sharepoint_agent/runtime/connections.py`: strict connection id validation.
- `src/sharepoint_agent/runtime/agent.py`: Foundry agent creation/reuse.
- `src/sharepoint_agent/evals/batch.py`: capture helper for evals.
