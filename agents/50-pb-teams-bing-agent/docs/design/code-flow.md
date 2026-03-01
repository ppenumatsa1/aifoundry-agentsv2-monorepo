CODE FLOW (ASCII ONLY)

STARTUP FLOW

+--------------------------------------------------+
| make run |
+--------------------------------------------------+
|
v
+--------------------------------------------------+
| scripts/run_agent.py |
| - load_dotenv(.env) |
| - settings = get_settings() |
| - uvicorn.run("teams_bing_agent.app:app") |
+--------------------------------------------------+
|
v
+--------------------------------------------------+
| import teams_bing_agent.app |
| - build FastAPI app + api_app |
| - configure auth mode |
| \* MSAL + JWT middleware OR anonymous fallback |
| - register POST /api/messages |
| - register message activity handler |
+--------------------------------------------------+

REQUEST FLOW (PER MESSAGE)

+--------------------------------------------------+
| Teams -> Bot Service |
| POST /api/messages |
+--------------------------------------------------+
|
v
+--------------------------------------------------+
| start_agent_process(...) |
| -> dispatch to on_message(...) |
+--------------------------------------------------+
|
v
+--------------------------------------------------+
| on_message |
| - read user text |
| - resolve conversation id |
| - call ask_with_conversation(...) |
+--------------------------------------------------+
|
v
+--------------------------------------------------+
| ask_with_conversation (runtime/run.py) |
| - get settings |
| - build project client |
| \* DefaultAzureCredential / Managed Identity |
| - get_or_create_agent(...) |
| - resolve/create conversation mapping |
| - openai_client.responses.create(...) |
| - extract response text |
+--------------------------------------------------+
|
v
+--------------------------------------------------+
| on_message |
| - context.send_activity(response) |
+--------------------------------------------------+
|
v
+--------------------------------------------------+
| Response back to Teams user |
+--------------------------------------------------+

MAIN FILES

- scripts/run_agent.py
- src/teams_bing_agent/app.py
- src/teams_bing_agent/config.py
- src/teams_bing_agent/runtime/run.py
- src/teams_bing_agent/runtime/openai_client.py
- src/teams_bing_agent/runtime/agent.py
- src/teams_bing_agent/runtime/state.py
