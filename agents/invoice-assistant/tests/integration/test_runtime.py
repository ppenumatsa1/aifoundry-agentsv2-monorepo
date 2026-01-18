import pytest

from invoice_assistant.runtime.run import ask


@pytest.mark.integration
def test_ask_smoke():
    # Requires Azure credentials in .env
    response = ask("What is the total amount for invoice INV-001?")
    assert response.answer
    assert response.top_documents
