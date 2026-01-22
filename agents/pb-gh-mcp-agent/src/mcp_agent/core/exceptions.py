class McpAgentError(Exception):
    """Base exception for the MCP agent."""


class McpApprovalRequiredError(McpAgentError):
    """Raised when MCP approval is required but auto-approval is disabled."""


class McpConfigError(McpAgentError):
    """Raised when MCP configuration is invalid."""
