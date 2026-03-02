# Code Flow

## End-to-end flow (implemented runtime path)

```text
+------------------+      +----------------------+      +---------------------------------------+
| Teams Client     | ---> | Azure Bot Service    | ---> | FastAPI /api/messages                 |
| (user message)   |      | (Connector pipeline) |      | (Microsoft Agents hosting)            |
+------------------+      +----------------------+      +---------------------------------------+
                                                                     |
                                                                     v
                                                      +-------------------------------+
                                                      | on_message handler            |
                                                      | - validate text               |
                                                      | - call runtime.ask(question)  |
                                                      +-------------------------------+
                                                                     |
                                                                     v
                                                      +-------------------------------+
                                                      | AIProjectClient               |
                                                      | (DefaultAzureCredential)      |
                                                      +-------------------------------+
                                                                     |
                                                                     v
                                                      +-------------------------------+
                                                      | Foundry responses.create      |
                                                      | (agent_reference)             |
                                                      +-------------------------------+
                                                                     |
                                                                     v
+------------------+      +----------------------+      +---------------------------------------+
| Teams Client     | <--- | Azure Bot Service    | <--- | FastAPI sends activity response       |
| (assistant text) |      |                      |      | from on_message                        |
+------------------+      +----------------------+      +---------------------------------------+

Auth path:
- Local: az login -> DefaultAzureCredential user token
- ACA: Managed Identity -> DefaultAzureCredential managed identity token
- Foundry authorization: RBAC (Azure AI User)

Behavior note:
- Runtime creates/updates the Foundry agent definition (instructions + web search tool) when needed, then invokes it.
- Agent identity is anchored by `FOUNDRY_AGENT_ID`.
```

## Startup flow

```text
make run
  -> scripts/run_agent.py
      -> load .env
      -> uvicorn teams_bing_agent.app:app
          -> FastAPI app mounted at /api/messages

Deployed startup (ACA)
  -> Container image entrypoint from Dockerfile CMD
     (command/args overrides are intentionally empty in ACA template)
  -> uvicorn teams_bing_agent.app:app
  -> /healthz and /api/messages served on port 8000
```

## Request flow with file + method mapping

```text
Teams/Bot Service
  -> POST /api/messages
    -> src/teams_bing_agent/app.py::messages()
      -> microsoft_agents.hosting.fastapi.start_agent_process(...)
      -> src/teams_bing_agent/app.py::on_message(...)
        -> validate non-empty user text
        -> src/teams_bing_agent/runtime/run.py::ask(question)
          -> src/teams_bing_agent/config.py::get_settings()
          -> src/teams_bing_agent/runtime/openai_client.py::build_project_client(settings)
               -> AIProjectClient(endpoint=AZURE_AI_PROJECT_ENDPOINT, credential=DefaultAzureCredential)
          -> src/teams_bing_agent/core/prompt_loader.py::load_prompt_text()
            -> loads src/teams_bing_agent/prompt.md instructions
          -> src/teams_bing_agent/runtime/agent.py::get_or_create_agent(project_client, settings, instructions)
            -> resolve_agent_name(settings) using FOUNDRY_AGENT_ID
            -> create_version(PromptAgentDefinition)
            -> attach WebSearchPreviewTool (Bing-backed web search)
            -> cache metadata in .foundry/agent.json
          -> openai_client.responses.create(input=question, extra_body.agent_reference)
          -> src/teams_bing_agent/runtime/run.py::_extract_response_text(response)
        -> send response back to Teams
```

## Key runtime modules

- `src/teams_bing_agent/app.py`: FastAPI host + message handler
- `src/teams_bing_agent/config.py`: environment settings
- `src/teams_bing_agent/runtime/run.py`: Foundry call + response extraction
- `src/teams_bing_agent/runtime/openai_client.py`: credentialed project client
- `src/teams_bing_agent/runtime/agent.py`: agent get/create + web-search tool wiring
- `src/teams_bing_agent/core/prompt_loader.py`: instruction loading from `prompt.md`

## Deployment and packaging flow

```text
Repo root
  -> azd provision --preview
  -> azd provision
  -> azd deploy
    -> builds/pushes app image to ACR
    -> updates ACA revision

agents/50-pb-teams-bing-agent
  -> make teams-package
    -> teams/build_teams_package.py reads .env
    -> writes teams/build/teams-app-package.zip
    -> upload zip to Teams Developer Portal
```

## Simplifications applied

- Removed provision-time bootstrap server pattern; runtime now always uses app image entrypoint.
- Consolidated infra under root `infra/` + `azd` flow.
- Added Teams channel provisioning in IaC (`MsTeamsChannel`) to remove portal-only manual step.
- Kept minimal FastAPI + Microsoft Agents hosting path (`/api/messages` + auth middleware).
