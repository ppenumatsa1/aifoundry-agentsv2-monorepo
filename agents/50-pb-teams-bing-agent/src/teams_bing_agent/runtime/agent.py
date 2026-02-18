from __future__ import annotations

import hashlib
import json

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    ApproximateLocation,
    PromptAgentDefinition,
    WebSearchPreviewTool,
)

from teams_bing_agent.config import Settings
from teams_bing_agent.runtime.cache import load_agent_cache, save_agent_cache


def _agent_fingerprint(settings: Settings, instructions: str) -> str:
    payload = {
        "agent_name": settings.foundry_agent_id,
        "instructions_hash": hashlib.sha256(instructions.encode("utf-8")).hexdigest(),
        "model": settings.azure_openai_model,
        "web_search_context_size": settings.web_search_context_size,
        "web_search_country": settings.web_search_country,
        "web_search_region": settings.web_search_region,
        "web_search_city": settings.web_search_city,
        "web_search_timezone": settings.web_search_timezone,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _build_web_search_tool(settings: Settings) -> WebSearchPreviewTool:
    kwargs: dict[str, object] = {}

    if settings.web_search_context_size:
        context_size = settings.web_search_context_size.strip().lower()
        if context_size not in {"low", "medium", "high"}:
            raise ValueError("WEB_SEARCH_CONTEXT_SIZE must be one of: low, medium, high")
        kwargs["search_context_size"] = context_size

    has_any_location = any(
        [
            settings.web_search_country,
            settings.web_search_region,
            settings.web_search_city,
            settings.web_search_timezone,
        ]
    )
    if has_any_location:
        kwargs["user_location"] = ApproximateLocation(
            country=settings.web_search_country,
            region=settings.web_search_region,
            city=settings.web_search_city,
            timezone=settings.web_search_timezone,
        )

    return WebSearchPreviewTool(**kwargs)


def get_or_create_agent(
    project_client: AIProjectClient,
    settings: Settings,
    instructions: str,
) -> str:
    web_search_tool = _build_web_search_tool(settings)

    cache = load_agent_cache()
    tool_hash = _agent_fingerprint(settings, instructions)

    agent_name = settings.foundry_agent_id
    agent_version = None
    if cache and cache.get("tool_hash") == tool_hash:
        agent_name = cache.get("agent_name", agent_name)
        agent_version = cache.get("agent_version")

    if not agent_version:
        agent = project_client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=settings.azure_openai_model,
                instructions=instructions,
                tools=[web_search_tool],
            ),
        )
        save_agent_cache(agent.name, agent.version, tool_hash)

    return agent_name
