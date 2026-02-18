class SharepointAgentError(Exception):
    """Base exception for the SharePoint agent."""


class SharepointConfigError(SharepointAgentError):
    """Raised when SharePoint agent configuration is invalid."""
