from __future__ import annotations

from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from invoice_assistant.config import Settings
from invoice_assistant.core.logging import get_logger
from invoice_assistant.ingest.cache import (
    load_cached_vector_store_id,
    save_vector_store_id,
)
from invoice_assistant.ingest.upload import upload_invoices
from invoice_assistant.core.paths import get_agent_root


def ingest_invoices(settings: Settings) -> None:
    logger = get_logger(__name__)
    endpoint = settings.azure_projects_endpoint
    cached_id = load_cached_vector_store_id()
    if cached_id:
        logger.info("cached_vector_store_id=%s", cached_id)

    credential = DefaultAzureCredential()
    project_client = AIProjectClient(endpoint=endpoint, credential=credential)

    with project_client.get_openai_client() as openai_client:
        if cached_id:
            try:
                openai_client.vector_stores.retrieve(cached_id)
                logger.info("reuse_vector_store_id=%s", cached_id)
                return
            except Exception as exc:
                logger.info(
                    "cached_vector_store_lookup_failed type=%s message=%s",
                    type(exc).__name__,
                    exc,
                )

        logger.info("creating_vector_store")
        vector_store = openai_client.vector_stores.create(name=settings.invoice_vectorstore_name)
        logger.info("vector_store_created id=%s", vector_store.id)

        invoice_dir = get_agent_root() / "data" / "invoices"
        upload_invoices(openai_client, vector_store.id, invoice_dir)

    save_vector_store_id(vector_store.id)
    logger.info("vector_store_ready id=%s", vector_store.id)
