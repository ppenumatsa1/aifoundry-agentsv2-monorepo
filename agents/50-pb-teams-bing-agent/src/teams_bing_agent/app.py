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
    Authorization,
    MemoryStorage,
    MessageFactory,
    TurnContext,
    TurnState,
)

from teams_bing_agent.config import Settings, get_settings
from teams_bing_agent.runtime.run import ask


def _is_configured(value: str | None) -> bool:
    if not value:
        return False
    stripped = value.strip()
    return bool(stripped) and not stripped.startswith("<")


def _configure_agents_sdk_environment(settings: Settings) -> dict:
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


def _load_environment() -> None:
    env_file = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(env_file)


_load_environment()
settings = get_settings()
agents_sdk_config = _configure_agents_sdk_environment(settings)

has_connection_config = bool(agents_sdk_config.get("CONNECTIONS")) and all(
    [
        _is_configured(environ.get("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID")),
        _is_configured(environ.get("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET")),
        _is_configured(environ.get("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID")),
    ]
)

storage = MemoryStorage()

app = FastAPI(title="pb-teams-bing-agent")
api_app = FastAPI()

if not has_connection_config:
    raise ValueError(
        "MICROSOFT_APP_ID, MICROSOFT_APP_PASSWORD, and MICROSOFT_APP_TENANT_ID must be set"
    )

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
