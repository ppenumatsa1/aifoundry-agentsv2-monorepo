from invoice_assistant.config import get_settings
from invoice_assistant.ingest.index import ingest_invoices


def main() -> None:
    settings = get_settings()
    ingest_invoices(settings)


if __name__ == "__main__":
    main()
