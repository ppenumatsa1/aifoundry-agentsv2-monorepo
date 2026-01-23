from __future__ import annotations

import re

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


def _embed_text(embedding_client: AzureOpenAI, model: str, text: str) -> list[float]:
    response = embedding_client.embeddings.create(model=model, input=[text])
    return list(response.data[0].embedding)


def ingest_documents(settings: Settings) -> None:
    logger = get_logger(__name__)
    ensure_index(settings)
    ensure_knowledge_source(settings)
    ensure_knowledge_base(settings)

    doc_dir = get_agent_root() / "data" / "insurance-docs"
    chunks = load_documents(doc_dir, settings.chunk_size, settings.chunk_overlap)

    credential = DefaultAzureCredential()
    embedding_client = _build_embedding_client(settings)

    search_client = SearchClient(
        endpoint=settings.search_endpoint,
        index_name=settings.search_index_name,
        credential=credential,
    )

    batch: list[dict] = []
    for chunk in chunks:
        embedding = _embed_text(embedding_client, settings.embedding_model, chunk.content)
        raw_id = f"{chunk.source}-{chunk.chunk_id}"
        safe_id = re.sub(r"[^A-Za-z0-9_\-=]", "_", raw_id)
        batch.append(
            {
                "id": safe_id,
                "content": chunk.content,
                "source": chunk.source,
                "chunk": chunk.chunk_id,
                "embedding": embedding,
            }
        )

        if len(batch) >= 50:
            result = search_client.upload_documents(batch)
            logger.info("uploaded_documents count=%s", len(result))
            batch = []

    if batch:
        result = search_client.upload_documents(batch)
        logger.info("uploaded_documents count=%s", len(result))

    logger.info("index_ready name=%s chunks=%s", settings.search_index_name, len(chunks))
