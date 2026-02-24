from __future__ import annotations

import hashlib
import json

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    ApproximateLocation,
    PromptAgentDefinition,
    WebSearchPreviewTool,
)

from teams_bing_agent.config import Settings, get_settings
from teams_bing_agent.core.prompt_loader import load_prompt_text
from teams_bing_agent.runtime.cache import load_agent_cache, save_agent_cache
from teams_bing_agent.runtime.openai_client import build_project_client


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


def main() -> None:
    settings = get_settings()
    instructions = load_prompt_text()
    project_client = build_project_client(settings)

    agent_name = get_or_create_agent(
        project_client=project_client,
        settings=settings,
        instructions=instructions,
    )

    cache = load_agent_cache() or {}
    print(f"agent_name={agent_name}")
    if cache.get("agent_version"):
        print(f"agent_version={cache['agent_version']}")
    if settings.azure_openai_model:
        print(f"model={settings.azure_openai_model}")


if __name__ == "__main__":
    main()
