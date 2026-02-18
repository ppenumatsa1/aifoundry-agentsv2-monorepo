# Architecture

- Ingestion layer uses Azure AI Projects vector stores.
- Runtime layer uses file_search tool via the agent to retrieve context.
- Azure OpenAI Responses API generates strict JSON which is schema-validated.
- Authentication uses DefaultAzureCredential (no API keys).
- Local cache stored in `.foundry/` for vector store and agent reuse.
- Orchestrator runs ingest, smoke query, batch capture, and evaluations in sequence.
- Evaluation pipeline captures batch runs into JSONL and submits Foundry evals.
- Evaluation datasets live in `src/invoice_assistant/evals/datasets/`.
- OpenTelemetry exports traces/metrics/logs to Azure Monitor for Agents view.
