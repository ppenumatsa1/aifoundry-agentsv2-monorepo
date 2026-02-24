# pb-teams-bing-agent Architecture

## System diagram

```text
                         +--------------------------------+
                         |            Clients             |
                         |--------------------------------|
                         | - Microsoft Teams User         |
                         | - M365 Agents Playground       |
                         | - cURL ActivityProtocol Test   |
                         +----------------+---------------+
                                      |
             Teams / Playground to app path   |
                                      v
+--------------------------------------------------------------------------+
|                 pb-teams-bing-agent (this repo)                          |
|--------------------------------------------------------------------------|
|  FastAPI /api/messages                                                   |
|      -> Agents SDK Adapter + Auth Middleware                             |
|          -> Runtime: ask_with_conversation                               |
|              -> ConversationStateStore (in-memory map)                   |
+-------------------------------+------------------------------------------+
                        |
                        v
              +---------------------------------------------+
              |             Azure AI Foundry               |
              |---------------------------------------------|
              | Project OpenAI Client / Responses API       |
              |     -> Foundry Agent Version                |
              |         -> Web Search Tool                  |
              +---------------------+-----------------------+
                              ^
                              |
                cURL direct path   |
                              |
              +---------------------+-----------------------+
              | Published Agent App Endpoint                |
              | (/protocols/activityprotocol)               |
              +---------------------------------------------+
```

## Flow explained

### 1) Current app flow (already tested)

1. User sends a message from **M365 Agents Playground** (or later Teams) to `POST /api/messages`.
2. FastAPI hands the activity to the Microsoft Agents SDK (`start_agent_process`).
3. Message handler in `src/teams_bing_agent/app.py` extracts text and Teams conversation ID.
4. Runtime `ask_with_conversation(...)` in `src/teams_bing_agent/runtime/run.py`:
   - Resolves app settings.
   - Gets or creates the Foundry agent version with Web Search tool.
   - Reuses or creates a Foundry conversation and stores mapping in `ConversationStateStore`.
   - Calls Foundry Responses API with `agent_reference`.
5. Foundry agent may call Web Search tool and returns response text.
6. Bot sends final text back as activity response.

### 2) Direct published endpoint flow (connectivity test)

1. `curl` posts an Activity payload directly to the published Foundry endpoint:
   - `/applications/{app}/protocols/activityprotocol?api-version=2025-11-15-preview`
2. Foundry handles Activity Protocol ingress and routes to the published agent.
3. Agent executes and returns a protocol response.

## Important behavior/constraints

- Conversation mapping is currently **in-memory**, so it resets when the process restarts.
- There are effectively two ingress choices:
  - **Your FastAPI app ingress** (`/api/messages`) — where your custom runtime logic runs.
  - **Published Foundry ActivityProtocol ingress** — bypasses your FastAPI layer.
- Authentication mode of the published application (RBAC vs Channels) determines which token works for direct `curl` invocation.

## How this helps next steps

- If the goal is **Teams -> your custom runtime -> Foundry**, integrate Teams/Bot channel with your FastAPI endpoint.
- If the goal is **Teams -> published Foundry app directly**, focus on Foundry publish/channel auth config and Teams binding.
- We can now choose one target path and implement only the required changes for it.
