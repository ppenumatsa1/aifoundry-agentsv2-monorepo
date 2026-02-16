# User Flow

1. Ingest invoice documents into a vector store.
2. Create or reuse an agent with file_search over the vector store (cached in `.foundry/`).
3. Ask a question; retrieve top documents via file_search.
4. Generate strict JSON output via Azure OpenAI Responses API.
5. Validate JSON response against `schema.json`.
6. Run batch questions to capture evaluation dataset.
7. Submit Foundry evaluation run on the captured dataset.
8. Export traces/metrics/logs to Azure Monitor for Agent runs visibility.
