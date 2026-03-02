from __future__ import annotations


class TeamsBingAgentError(Exception):
    """Base exception for the Teams Bing agent."""


class TeamsBingApprovalRequiredError(TeamsBingAgentError):
    """Raised when approval is required but auto-approval is disabled."""


class TeamsBingConfigError(TeamsBingAgentError):
    """Raised when Teams Bing agent configuration is invalid."""
