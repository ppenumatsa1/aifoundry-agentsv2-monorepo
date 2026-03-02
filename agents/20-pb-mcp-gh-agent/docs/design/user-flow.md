# User Flow

1. Operator configures `.env` with Foundry endpoint/model and MCP settings.
2. User asks a question via `scripts/run_agent.py`.
3. Runtime resolves/creates project connection to MCP server.
4. Runtime resolves/creates Foundry agent and starts a conversation.
5. Agent invokes MCP tool calls as needed.
6. Approval loop auto-approves MCP requests when enabled.
7. Final assistant response is extracted and returned.
8. Optional: run batch questions and Foundry evaluators using scripts.
