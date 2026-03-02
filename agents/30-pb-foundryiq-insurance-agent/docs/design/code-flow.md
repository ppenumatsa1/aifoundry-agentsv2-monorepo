# Code Flow

## End-to-end ASCII diagram

```text
+-------------------+      +--------------------------+      +-------------------------------+
| CLI user          | ---> | scripts/run_agent.py     | ---> | runtime/run.py::_run_agent()  |
| (insurance query) |      |                          |      |                               |
+-------------------+      +--------------------------+      +---------------+---------------+
                                |
                                v
                          +-------------------------------+
                          | Foundry responses.create      |
                          | tool_choice='required' (MCP)  |
                          +---------------+---------------+
                              |
                        success              | failure (401/tool/timeout)
                          |               v
                          |   +----------------------------+
                          |   | fallback_search_context()  |
                          |   | SearchClient + synthesize  |
                          |   +-------------+--------------+
                          v                 |
                  +---------------------------+   |
                  | _extract_response_text()  |<--+
                  +-------------+-------------+
                          |
                          v
                  +---------------------------+
                  | CLI output                |
                  +---------------------------+
```

## Ingestion flow

```text
scripts/ingest_documents.py
  -> ingest/index.py::ingest_documents()
    -> ensure_index()
    -> ensure_knowledge_source()
    -> ensure_knowledge_base()
    -> load_documents() from data/insurance-docs
    -> embedding generation
    -> batched upload to Azure AI Search
```

## Runtime ask flow

```text
scripts/run_agent.py
  -> runtime/run.py::ask_with_metadata()
    -> build_project_client()
    -> ensure_project_connection()
    -> get_or_create_agent(... MCP config ...)
    -> responses.create(tool_choice='required')
    -> approval loop
    -> _extract_response_text()
```

## Fallback flow (when MCP fails)

```text
runtime/run.py::_run_agent()
  -> catch MCP/tool/auth/timeouts
  -> _fallback_answer_with_search_context()
     -> SearchClient.search()
     -> compose grounded context
     -> responses.create(model=azure_openai_model)
```

## Evaluation flow

- `scripts/run_batch_questions.py` -> capture dataset
- `scripts/run_foundry_evaluations.py` -> evaluator run
- `scripts/run_orchestrator.py` -> end-to-end script pipeline
