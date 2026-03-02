# User Flow

1. User sends a message in Microsoft Teams.
2. Azure Bot Service receives the activity and forwards it to `POST /api/messages`.
3. FastAPI + Microsoft Agents hosting middleware validates/authenticates the incoming Bot request.
4. `on_message` handler validates text input and calls runtime `ask(question)`.
5. Runtime builds Foundry project client using `DefaultAzureCredential`.
6. Runtime resolves/creates the configured Foundry agent and invokes `responses.create`.
7. Foundry agent optionally uses web search tooling, then returns response content.
8. App sends assistant text back through Bot Service to Teams.
9. Telemetry for business events and dependencies is emitted to App Insights when enabled.
10. Operators run KQL scripts under `scripts/kusto/` for business-event, dependency, and exception checks.
