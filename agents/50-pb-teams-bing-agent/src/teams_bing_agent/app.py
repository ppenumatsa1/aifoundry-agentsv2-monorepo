from __future__ import annotations

import asyncio
from os import environ
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.fastapi import (
    CloudAdapter,
    JwtAuthorizationMiddleware,
    start_agent_process,
)
from microsoft_agents.hosting.core import (
    AgentApplication,
    AgentAuthConfiguration,
    Authorization,
    MemoryStorage,
    MessageFactory,
    TurnContext,
    TurnState,
)

from teams_bing_agent.config import get_settings
from teams_bing_agent.runtime.run import ask_with_conversation
from teams_bing_agent.runtime.state import ConversationStateStore


class AnonymousConnectionManager:
    def __init__(self) -> None:
        self._provider = _LocalDevTokenProvider()

    def get_connection(self, _connection_name: str):
        return self._provider

    def get_default_connection(self):
        return self._provider

    def get_token_provider(self, _claims_identity, _service_url: str):
        return self._provider

    def get_default_connection_configuration(self) -> AgentAuthConfiguration:
        return AgentAuthConfiguration()


class _LocalDevTokenProvider:
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


def _configure_agents_sdk_environment() -> dict:
    env_file = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(env_file)
    settings = get_settings()

    client_id_key = "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID"
    client_secret_key = "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET"
    tenant_id_key = "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID"

    if not environ.get(client_id_key) and settings.microsoft_app_id:
        environ[client_id_key] = settings.microsoft_app_id
    if not environ.get(client_secret_key) and settings.microsoft_app_password:
        environ[client_secret_key] = settings.microsoft_app_password
    if not environ.get(tenant_id_key) and settings.microsoft_app_tenant_id:
        environ[tenant_id_key] = settings.microsoft_app_tenant_id

    return load_configuration_from_env(environ)


def _is_configured(value: str | None) -> bool:
    if not value:
        return False
    stripped = value.strip()
    return bool(stripped) and not stripped.startswith("<")


agents_sdk_config = _configure_agents_sdk_environment()
storage = MemoryStorage()
has_connection_config = bool(agents_sdk_config.get("CONNECTIONS")) and all(
    [
        _is_configured(environ.get("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID")),
        _is_configured(environ.get("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET")),
        _is_configured(environ.get("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID")),
    ]
)

app = FastAPI(title="pb-teams-bing-agent")
api_app = FastAPI()

if has_connection_config:
    connection_manager = MsalConnectionManager(**agents_sdk_config)
    api_app.add_middleware(JwtAuthorizationMiddleware)
    api_app.state.agent_configuration = connection_manager.get_default_connection_configuration()

    adapter = CloudAdapter(connection_manager=connection_manager)
    authorization = Authorization(storage, connection_manager, **agents_sdk_config)
    agent_app = AgentApplication[TurnState](
        storage=storage,
        adapter=adapter,
        authorization=authorization,
        **agents_sdk_config,
    )
else:
    connection_manager = AnonymousConnectionManager()
    adapter = CloudAdapter(connection_manager=connection_manager)
    agent_app = AgentApplication[TurnState](storage=storage, adapter=adapter)

state_store = ConversationStateStore()


@agent_app.activity("message")
async def on_message(context: TurnContext, _state: TurnState):
    message_text = (context.activity.text or "").strip()
    if not message_text:
        await context.send_activity(MessageFactory.text("Please send a text message."))
        return

    conversation = getattr(context.activity, "conversation", None)
    teams_conversation_id = getattr(conversation, "id", None)
    if not isinstance(teams_conversation_id, str) or not teams_conversation_id.strip():
        from_property = getattr(context.activity, "from_property", None)
        sender_id = getattr(from_property, "id", "anonymous")
        teams_conversation_id = f"fallback:{sender_id}"

    result = await asyncio.to_thread(
        ask_with_conversation,
        message_text,
        teams_conversation_id,
        state_store,
    )

    response_text = result.response_text or "I could not generate a response."
    await context.send_activity(MessageFactory.text(response_text))


@api_app.post("/messages")
async def messages(request: Request):
    return await start_agent_process(request, agent_app, adapter)


app.mount("/api", api_app)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
