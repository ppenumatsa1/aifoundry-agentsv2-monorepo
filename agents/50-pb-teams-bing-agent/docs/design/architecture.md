# pb-teams-bing-agent Architecture

## Target system

```text
REQUEST / RESPONSE PATH

+------------------+      +-------------------------------------+
| Teams User       | ---> | Azure Bot Service                   |
| (Teams client)   |      | (Bot Registration + Teams channel)  |
+------------------+      +-------------------------------------+
                                   |
                                   | HTTPS POST /api/messages
                                   v
                    +-------------------------------------+
                    | ACA-hosted M365 SDK app             |
                    | (this repo, FastAPI endpoint)       |
                    +-------------------------------------+
                                   |
                                   | Managed Identity token
                                   v
                    +-------------------------------------+
                    | Azure AI Foundry Agent Endpoint     |
                    | (LLM + Web Search tool)             |
                    +-------------------------------------+
                                   |
                                   | response text
                                   v
                    +-------------------------------------+
                    | Back through Bot Service to Teams   |
                    +-------------------------------------+


IDENTITY BOUNDARIES

+---------------------------------------------------------+
| Teams/Bot auth boundary                                 |
| - Bot App Registration identity                         |
| - JWT validation handled by M365 SDK middleware         |
+---------------------------------------------------------+

+---------------------------------------------------------+
| Foundry access boundary                                 |
| - ACA Managed Identity                                  |
| - No OBO flow                                           |
+---------------------------------------------------------+
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
