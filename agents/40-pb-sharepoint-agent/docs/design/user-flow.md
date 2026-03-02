# User Flow

1. Operator configures `.env` with Foundry endpoint/model and `SHAREPOINT_CONNECTION_ID`.
2. User asks a question via `scripts/run_agent.py`.
3. Runtime validates SharePoint connection id format.
4. Runtime resolves/creates Foundry agent bound to SharePoint grounding tool.
5. Conversation and response are executed through Foundry responses API.
6. Assistant response is extracted and returned.
7. Optional: batch capture and Foundry evaluator scripts are run.
