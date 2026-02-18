from __future__ import annotations

from pathlib import Path

from invoice_assistant.core.logging import get_logger


def upload_invoices(openai_client, vector_store_id: str, invoice_dir: Path) -> None:
    logger = get_logger(__name__)
    files = sorted(invoice_dir.glob("*.txt"))
    if not files:
        raise ValueError(f"No invoice files found in {invoice_dir}")

    logger.info("uploading_invoices count=%s", len(files))
    for file_path in files:
        with open(file_path, "rb") as handle:
            openai_client.vector_stores.files.upload_and_poll(
                vector_store_id=vector_store_id,
                file=handle,
            )
    logger.info("uploaded_invoices count=%s", len(files))
