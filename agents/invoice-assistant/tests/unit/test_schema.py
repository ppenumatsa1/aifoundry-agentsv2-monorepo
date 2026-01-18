from invoice_assistant.schema import InvoiceAssistantResponse


def test_schema_roundtrip():
    data = {
        "answer": "The total amount for invoice INV-001 is $1200.00.",
        "top_documents": [
            {
                "doc_id": "inv-001",
                "file_name": "INV-001.pdf",
                "snippet": "Total: $1200.00",
            }
        ],
    }
    model = InvoiceAssistantResponse.model_validate(data)
    assert model.answer
