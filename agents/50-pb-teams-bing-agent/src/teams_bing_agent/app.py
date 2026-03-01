from __future__ import annotations

import asyncio
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from microsoft_agents.hosting.fastapi import (
    CloudAdapter,
    start_agent_process,
)
from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    MessageFactory,
    TurnContext,
    TurnState,
)

from teams_bing_agent.config import get_settings
from teams_bing_agent.runtime.run import ask


class _NoopTokenProvider:
    async def get_access_token(
        self, resource_url: str, scopes: list[str], force_refresh: bool = False
    ) -> str:
        return "local-dev-token"

    async def acquire_token_on_behalf_of(self, assertion: str, scopes: list[str]):
        return {"access_token": "local-dev-token"}

    async def get_agentic_application_token(self, scopes: list[str]) -> str:
        return "local-dev-token"

    async def get_agentic_instance_token(self, scopes: list[str]) -> str:
        return "local-dev-token"

    async def get_agentic_user_token(self, user_assertion: str, scopes: list[str]) -> str:
        return "local-dev-token"


class _NoopConnectionManager:
    def __init__(self) -> None:
        self._provider = _NoopTokenProvider()

    def get_connection(self, _connection_name: str):
        return self._provider

    def get_default_connection(self):
        return self._provider

    def get_token_provider(self, _claims_identity, _service_url: str):
        return self._provider


def _load_environment() -> None:
    env_file = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(env_file)


_load_environment()
settings = get_settings()
storage = MemoryStorage()

app = FastAPI(title="pb-teams-bing-agent")
api_app = FastAPI()

adapter = CloudAdapter(connection_manager=_NoopConnectionManager())
agent_app = AgentApplication[TurnState](storage=storage, adapter=adapter)


@agent_app.activity("message")
async def on_message(context: TurnContext, _state: TurnState):
    message_text = (context.activity.text or "").strip()
    if not message_text:
        await context.send_activity(MessageFactory.text("Please send a text message."))
        return

    result = await asyncio.to_thread(
        ask,
        message_text,
    )

    response_text = result.response_text or "I could not generate a response."
    await context.send_activity(MessageFactory.text(response_text))


@api_app.post("/messages")
async def messages(request: Request):
    return await start_agent_process(request, agent_app, adapter)


app.mount("/api", api_app)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    endpoint_set = bool(settings.azure_projects_endpoint)
    return {"status": "ok" if endpoint_set else "misconfigured"}
