from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from os import environ
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
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
from opentelemetry import trace

from teams_bing_agent.config import Settings, get_settings
from teams_bing_agent.core.exceptions import TeamsBingAgentError, TeamsBingConfigError
from teams_bing_agent.core.logging import get_logger
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


def _extract_tenant_id(channel_data: object) -> str | None:
    if isinstance(channel_data, dict):
        tenant = channel_data.get("tenant")
        if isinstance(tenant, dict):
            tenant_id = tenant.get("id")
            if isinstance(tenant_id, str):
                return tenant_id
    return None


_load_environment()
settings = get_settings()
agents_sdk_config = _configure_agents_sdk_environment(settings)
logger = get_logger("teams_bing_agent.app")
tracer = trace.get_tracer(__name__)

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
    raise TeamsBingConfigError(
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


def _configure_exception_handlers(target: FastAPI) -> None:
    handler_logger = get_logger("teams_bing_agent.exceptions")

    @target.exception_handler(TeamsBingAgentError)
    async def handle_agent_error(request: Request, exc: TeamsBingAgentError) -> JSONResponse:
        handler_logger.warning(
            "agent_error",
            extra={
                "event": "agent_error",
                "flow_stage": "fastapi_exception_handler",
                "request_path": request.url.path,
                "method": request.method,
                "status_code": exc.status_code,
                "success": False,
                "error_code": exc.code,
                "error_type": type(exc).__name__,
            },
        )
        return JSONResponse(status_code=exc.status_code, content={"error": exc.to_dict()})

    @target.exception_handler(Exception)
    async def handle_unhandled_error(request: Request, exc: Exception) -> JSONResponse:
        handler_logger.exception(
            "unhandled_error",
            extra={
                "event": "unhandled_error",
                "flow_stage": "fastapi_exception_handler",
                "request_path": request.url.path,
                "method": request.method,
                "status_code": 500,
                "success": False,
                "error_code": "internal_error",
                "error_type": type(exc).__name__,
            },
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "Internal server error",
                }
            },
        )


@agent_app.activity("message")
async def on_message(context: TurnContext, _state: TurnState):
    activity = context.activity
    message_text = (activity.text or "").strip()
    conversation_id = getattr(getattr(activity, "conversation", None), "id", None)
    channel_id = getattr(activity, "channel_id", None)
    tenant_id = _extract_tenant_id(getattr(activity, "channel_data", None))

    if not message_text:
        logger.info(
            "message_empty",
            extra={
                "event": "message_empty",
                "flow_stage": "activity_validation",
                "success": False,
                "conversation_id": conversation_id,
                "channel_id": channel_id,
                "tenant_id": tenant_id,
            },
        )
        await context.send_activity(MessageFactory.text("Please send a text message."))
        return

    started_at = datetime.now(UTC)
    with tracer.start_as_current_span("teams.on_message") as span:
        span.set_attribute("app.flow.stage", "fastapi_to_foundry")
        span.set_attribute("gen_ai.user.message.length", len(message_text))
        try:
            result = await asyncio.to_thread(
                ask,
                message_text,
            )
            elapsed_ms = int((datetime.now(UTC) - started_at).total_seconds() * 1000)
            span.set_attribute("app.flow.duration_ms", elapsed_ms)
            if result.response_id:
                span.set_attribute("gen_ai.response.id", result.response_id)
            logger.info(
                "message_completed",
                extra={
                    "event": "message_completed",
                    "flow_stage": "fastapi_to_foundry",
                    "success": True,
                    "duration_ms": elapsed_ms,
                    "foundry_response_id": result.response_id,
                    "conversation_id": conversation_id,
                    "channel_id": channel_id,
                    "tenant_id": tenant_id,
                },
            )
        except Exception as exc:
            logger.exception(
                "message_failed",
                extra={
                    "event": "message_failed",
                    "flow_stage": "fastapi_to_foundry",
                    "success": False,
                    "error_type": type(exc).__name__,
                    "conversation_id": conversation_id,
                    "channel_id": channel_id,
                    "tenant_id": tenant_id,
                },
            )
            raise

    response_text = result.response_text or "I could not generate a response."
    await context.send_activity(MessageFactory.text(response_text))


@api_app.post("/messages")
async def messages(request: Request):
    with tracer.start_as_current_span("teams.messages_endpoint") as span:
        span.set_attribute("http.route", "/api/messages")
        try:
            response = await start_agent_process(request, agent_app, adapter)
            status_code = getattr(response, "status_code", None)
            logger.info(
                "messages_endpoint_completed",
                extra={
                    "event": "messages_endpoint_completed",
                    "flow_stage": "fastapi_ingress",
                    "request_path": request.url.path,
                    "method": request.method,
                    "status_code": status_code,
                    "success": True,
                },
            )
            return response
        except Exception as exc:
            logger.exception(
                "messages_endpoint_failed",
                extra={
                    "event": "messages_endpoint_failed",
                    "flow_stage": "fastapi_ingress",
                    "request_path": request.url.path,
                    "method": request.method,
                    "success": False,
                    "error_type": type(exc).__name__,
                },
            )
            raise


app.mount("/api", api_app)
_configure_exception_handlers(api_app)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    endpoint_set = bool(settings.azure_projects_endpoint)
    return {"status": "ok" if endpoint_set else "misconfigured"}
