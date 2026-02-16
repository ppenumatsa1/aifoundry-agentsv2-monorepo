class InsuranceAgentError(Exception):
    pass


class McpConfigError(InsuranceAgentError):
    pass


class McpApprovalRequiredError(InsuranceAgentError):
    pass
