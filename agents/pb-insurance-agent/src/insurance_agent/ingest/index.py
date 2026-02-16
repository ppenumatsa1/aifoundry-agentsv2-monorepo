from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
import re
import time
from typing import Iterable, Sequence

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    KnowledgeBase,
    KnowledgeRetrievalMinimalReasoningEffort,
    KnowledgeRetrievalOutputMode,
    KnowledgeSourceReference,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SearchIndexFieldReference,
    SearchIndexKnowledgeSource,
    SearchIndexKnowledgeSourceParameters,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from openai import AzureOpenAI

from insurance_agent.config import Settings
from insurance_agent.core.logging import get_logger
from insurance_agent.core.paths import get_agent_root
from insurance_agent.ingest.loaders import load_documents


def _batched(values: Sequence, batch_size: int) -> Iterable[Sequence]:
    size = max(1, batch_size)
    for index in range(0, len(values), size):
        yield values[index : index + size]


def _build_index(settings: Settings) -> SearchIndex:
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchField(
            name="content",
            type=SearchFieldDataType.String,
            searchable=True,
        ),
        SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="chunk", type=SearchFieldDataType.Int32, filterable=True),
        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=settings.search_vector_dim,
            vector_search_profile_name="vector-profile",
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
        profiles=[VectorSearchProfile(name="vector-profile", algorithm_configuration_name="hnsw")],
    )

    semantic_search = SemanticSearch(
        configurations=[
            SemanticConfiguration(
                name="semantic_config",
                prioritized_fields=SemanticPrioritizedFields(
                    content_fields=[SemanticField(field_name="content")]
                ),
            )
        ],
        default_configuration_name="semantic_config",
    )

    return SearchIndex(
        name=settings.search_index_name,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search,
    )


def ensure_index(settings: Settings) -> None:
    credential = DefaultAzureCredential()
    index_client = SearchIndexClient(settings.search_endpoint, credential=credential)
    index = _build_index(settings)
    index_client.create_or_update_index(index)


def ensure_knowledge_source(settings: Settings) -> None:
    credential = DefaultAzureCredential()
    index_client = SearchIndexClient(settings.search_endpoint, credential=credential)

    ks = SearchIndexKnowledgeSource(
        name=settings.knowledge_source_name,
        description="Knowledge source for insurance documents.",
        search_index_parameters=SearchIndexKnowledgeSourceParameters(
            search_index_name=settings.search_index_name,
            source_data_fields=[
                SearchIndexFieldReference(name="id"),
                SearchIndexFieldReference(name="source"),
                SearchIndexFieldReference(name="chunk"),
            ],
        ),
    )

    index_client.create_or_update_knowledge_source(knowledge_source=ks)


def ensure_knowledge_base(settings: Settings) -> None:
    credential = DefaultAzureCredential()
    index_client = SearchIndexClient(settings.search_endpoint, credential=credential)

    knowledge_base = KnowledgeBase(
        name=settings.knowledge_base_name,
        knowledge_sources=[KnowledgeSourceReference(name=settings.knowledge_source_name)],
        output_mode=KnowledgeRetrievalOutputMode.EXTRACTIVE_DATA,
        retrieval_reasoning_effort=KnowledgeRetrievalMinimalReasoningEffort(),
    )

    index_client.create_or_update_knowledge_base(knowledge_base=knowledge_base)


def _build_embedding_client(settings: Settings) -> AzureOpenAI:
    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default"
    )
    return AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
        azure_ad_token_provider=token_provider,
    )


def _embed_texts(
    embedding_client: AzureOpenAI, model: str, texts: list[str]
) -> list[list[float]]:
    response = embedding_client.embeddings.create(model=model, input=texts)
    return [list(item.embedding) for item in response.data]


def _upload_batch(
    endpoint: str,
    index_name: str,
    credential: DefaultAzureCredential,
    documents: list[dict],
) -> int:
    search_client = SearchClient(
        endpoint=endpoint,
        index_name=index_name,
        credential=credential,
    )
    result = search_client.upload_documents(documents)
    return len(result)


def ingest_documents(settings: Settings) -> None:
    logger = get_logger(__name__)
    started_at = time.perf_counter()

    ensure_index(settings)
    ensure_knowledge_source(settings)
    ensure_knowledge_base(settings)

    doc_dir = get_agent_root() / "data" / "insurance-docs"
    load_started = time.perf_counter()
    chunks = load_documents(doc_dir, settings.chunk_size, settings.chunk_overlap)
    load_seconds = time.perf_counter() - load_started

    credential = DefaultAzureCredential()
    embedding_client = _build_embedding_client(settings)

    embedding_batch_size = max(1, settings.embedding_batch_size)
    upload_batch_size = max(1, settings.upload_batch_size)
    max_parallel_uploads = max(1, settings.max_parallel_uploads)

    embedding_started = time.perf_counter()
    prepared_docs: list[dict] = []
    for chunk_batch in _batched(chunks, embedding_batch_size):
        texts = [chunk.content for chunk in chunk_batch]
        embeddings = _embed_texts(embedding_client, settings.embedding_model, texts)
        for chunk, embedding in zip(chunk_batch, embeddings, strict=True):
            raw_id = f"{chunk.source}-{chunk.chunk_id}"
            safe_id = re.sub(r"[^A-Za-z0-9_\-=]", "_", raw_id)
            prepared_docs.append(
                {
                    "id": safe_id,
                    "content": chunk.content,
                    "source": chunk.source,
                    "chunk": chunk.chunk_id,
                    "embedding": embedding,
                }
            )
    embedding_seconds = time.perf_counter() - embedding_started

    upload_started = time.perf_counter()
    upload_futures: list[Future[int]] = []
    uploaded_count = 0
    with ThreadPoolExecutor(max_workers=max_parallel_uploads) as executor:
        for doc_batch in _batched(prepared_docs, upload_batch_size):
            upload_futures.append(
                executor.submit(
                    _upload_batch,
                    settings.search_endpoint,
                    settings.search_index_name,
                    credential,
                    list(doc_batch),
                )
            )

            if len(upload_futures) >= max_parallel_uploads:
                done, pending = wait(upload_futures, return_when=FIRST_COMPLETED)
                upload_futures = list(pending)
                for future in done:
                    batch_uploaded = future.result()
                    uploaded_count += batch_uploaded
                    logger.info("uploaded_documents count=%s", batch_uploaded)

        for future in upload_futures:
            batch_uploaded = future.result()
            uploaded_count += batch_uploaded
            logger.info("uploaded_documents count=%s", batch_uploaded)

    upload_seconds = time.perf_counter() - upload_started
    total_seconds = time.perf_counter() - started_at

    logger.info(
        "index_ready name=%s chunks=%s uploaded=%s load_s=%.2f embed_s=%.2f upload_s=%.2f total_s=%.2f",
        settings.search_index_name,
        len(chunks),
        uploaded_count,
        load_seconds,
        embedding_seconds,
        upload_seconds,
        total_seconds,
    )
