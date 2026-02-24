CODE FLOW (ASCII ONLY)

+-------------------+
| make run |
+-------------------+
|
v
+------------------------------------------+
| .venv/bin/python scripts/run_agent.py |
+------------------------------------------+
|
v
+------------------------------------------+
| load_dotenv(.env) |
| settings = get_settings() |
| uvicorn.run("teams_bing_agent.app:app") |
+------------------------------------------+
|
v
+------------------------------------------+
| Import teams_bing_agent.app |
| - configure env mapping |
| - create FastAPI app + api_app |
| - auth mode: |
| _ Msal + JWT middleware OR |
| _ anonymous fallback |
| - register POST /api/messages |
| - register message activity handler |
+------------------------------------------+
|
v
+------------------------------------------+
| Teams/Bot Service POST /api/messages |
+------------------------------------------+
|
v
+------------------------------------------+
| start_agent_process(...) |
| -> dispatch to on_message(...) |
+------------------------------------------+
|
v
+------------------------------------------+
| on_message |
| - read text |
| - resolve teams_conversation_id |
| - call ask_with_conversation(...) |
+------------------------------------------+
|
v
+------------------------------------------+
| ask_with_conversation (runtime/run.py) |
| - settings = get_settings() |
| - build_project_client(...) |
| _ DefaultAzureCredential |
| _ AIProjectClient(endpoint=...) |
| - get_or_create_agent(...) |
| - resolve/create conversation mapping |
| - openai_client.responses.create(...) |
| - extract response text |
+------------------------------------------+
|
v
+------------------------------------------+
| on_message sends response |
| context.send_activity(text) |
+------------------------------------------+
|
v
+------------------------------------------+
| Response back to Teams user |
+------------------------------------------+

MAIN FILES

- scripts/run_agent.py
- src/teams_bing_agent/app.py
- src/teams_bing_agent/config.py
- src/teams_bing_agent/runtime/run.py
- src/teams_bing_agent/runtime/openai_client.py
- src/teams_bing_agent/runtime/agent.py
- src/teams_bing_agent/runtime/state.py
