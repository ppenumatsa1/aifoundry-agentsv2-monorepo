class InvoiceAssistantError(Exception):
    """Base exception for the invoice assistant."""


class VectorStoreNotFoundError(InvoiceAssistantError):
    """Raised when the vector store cache is missing."""
