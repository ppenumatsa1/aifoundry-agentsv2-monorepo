# Architecture

- Ingestion layer uses Azure AI Projects vector stores.
- Runtime layer uses file_search tool via the agent to retrieve context.
- Azure OpenAI Responses API generates strict JSON which is schema-validated.
- Authentication uses DefaultAzureCredential (no API keys).
- Local cache stored in `.foundry/` for vector store and agent reuse.
