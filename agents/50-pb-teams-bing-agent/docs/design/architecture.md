# pb-teams-bing-agent Architecture

## Target system

```text
User (Teams)
   -> Azure Bot Service (Bot Registration + Teams channel)
   -> HTTPS POST /api/messages
   -> ACA-hosted M365 SDK app (this repo)
   -> Managed Identity token acquisition
   -> Azure AI Foundry Agent Endpoint
   -> LLM + Web Search tool
   -> Response returns same path back to Teams
```

## Identity boundaries

- Bot App Registration identity is used for Teams/Bot authentication and JWT validation.
- Managed Identity on Azure Container Apps is used for Foundry authorization.
- App-only architecture: no OBO.

## Request flow

1. Teams sends bot activity to Azure Bot Service.
2. Bot Service forwards to `/api/messages` on ACA.
3. M365 Agents SDK validates bot JWT and routes the message handler.
4. Handler calls Foundry through `src/teams_bing_agent/runtime` modules.
5. Foundry response text is sent back through Bot Service to Teams.

## Runtime notes

- Local development uses developer credentials via `DefaultAzureCredential`.
- ACA runtime uses `ManagedIdentityCredential`.
- Conversation state map is in-memory and resets on restart.
