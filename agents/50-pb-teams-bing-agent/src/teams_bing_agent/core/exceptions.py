from __future__ import annotations


class TeamsBingAgentError(Exception):
    """Base exception for the Teams Bing agent."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "teams_bing_agent_error",
        status_code: int = 400,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.message = message

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


class TeamsBingApprovalRequiredError(TeamsBingAgentError):
    """Raised when approval is required but auto-approval is disabled."""

    def __init__(self, message: str = "Approval is required") -> None:
        super().__init__(message, code="approval_required", status_code=403)


class TeamsBingConfigError(TeamsBingAgentError):
    """Raised when Teams Bing agent configuration is invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="config_error", status_code=500)
