from __future__ import annotations

from sharepoint_agent.config import Settings
from sharepoint_agent.core.exceptions import SharepointConfigError
from sharepoint_agent.runtime.cache import load_connection_cache, save_connection_cache


def _is_connection_id(value: str) -> bool:
    return (
        value.startswith("/")
        and "/providers/" in value
        and "/connections/" in value
        and "Microsoft.MachineLearningServices" in value
    )


def ensure_project_connection(settings: Settings) -> str:
    configured = settings.sharepoint_connection_id.strip()
    if not configured:
        raise SharepointConfigError("SHAREPOINT_CONNECTION_ID must be set and non-empty")

    cached = load_connection_cache()
    if cached and cached.get("connection_id") == configured:
        return configured

    if not _is_connection_id(configured):
        raise SharepointConfigError(
            "SHAREPOINT_CONNECTION_ID must be the full Foundry project connection ARM resource ID"
        )

    save_connection_cache(configured, "sharepoint")
    return configured
