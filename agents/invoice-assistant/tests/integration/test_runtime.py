import pytest

from invoice_assistant.runtime.run import ask


@pytest.mark.integration
@pytest.mark.parametrize(
    "question",
    [
        "What is the total amount for invoice INV-1001?",
        "Who is the vendor listed on invoice INV-1002?",
        "What is the due date for invoice INV-1003?",
    ],
)
def test_ask_smoke(question: str):
    # Requires Azure credentials in .env
    response = ask(question)
    assert response.answer
    assert response.top_documents
