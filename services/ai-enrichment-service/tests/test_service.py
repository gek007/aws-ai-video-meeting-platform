from ai_enrichment_service.embedder import InMemoryEmbeddingGenerator
from ai_enrichment_service.indexer import InMemoryVectorIndexer
from ai_enrichment_service.publisher import InMemoryTopicPublisher
from ai_enrichment_service.generator import DeterministicEnrichmentGenerator
from ai_enrichment_service.store import InMemoryMetadataStore
from ai_enrichment_service.service import AIEnrichmentService


def test_ai_enrichment_service_returns_summary_topics_and_action_items():
    publisher = InMemoryTopicPublisher()
    metadata_store = InMemoryMetadataStore()
    result = AIEnrichmentService(
        publisher=publisher,
        metadata_store=metadata_store,
        generator=DeterministicEnrichmentGenerator(),
    ).enrich(
        {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
            "correlationId": "corr_123",
        }
    )

    assert result["eventType"] == "meeting.intelligence.generated"
    assert result["summary"] == "Meeting summary placeholder."
    assert "authentication" in result["topics"]
    assert result["actionItems"][0]["item_type"] == "bug"
    assert result["actionItems"][0]["actionItemId"].startswith("act_")
    assert result["taskProvider"] == "jira"
    assert result["modelId"] == "deterministic-placeholder"
    assert publisher.messages[0]["eventType"] == "meeting.intelligence.generated"
    assert metadata_store.records[0]["aiEnrichmentStatus"] == "completed"


def test_ai_enrichment_service_generates_and_indexes_embeddings():
    publisher = InMemoryTopicPublisher()
    metadata_store = InMemoryMetadataStore()
    embedding_generator = InMemoryEmbeddingGenerator()
    vector_indexer = InMemoryVectorIndexer()

    result = AIEnrichmentService(
        publisher=publisher,
        metadata_store=metadata_store,
        generator=DeterministicEnrichmentGenerator(),
        embedding_generator=embedding_generator,
        vector_indexer=vector_indexer,
    ).enrich(
        {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
            "correlationId": "corr_123",
            "transcriptText": "This is a long transcript about authentication and reliability. " * 20,
        }
    )

    assert len(result["transcriptChunks"]) > 0
    assert all("emb_inmemory_" in chunk["embeddingRef"] for chunk in result["transcriptChunks"])
    assert len(vector_indexer.documents) == len(result["transcriptChunks"])
    assert vector_indexer.documents[0]["tenantId"] == "tenant_123"
    assert vector_indexer.documents[0]["meetingId"] == "mtg_123"


def test_ai_enrichment_service_works_without_embedding_generator():
    publisher = InMemoryTopicPublisher()
    metadata_store = InMemoryMetadataStore()

    result = AIEnrichmentService(
        publisher=publisher,
        metadata_store=metadata_store,
        generator=DeterministicEnrichmentGenerator(),
    ).enrich(
        {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
            "correlationId": "corr_123",
        }
    )

    assert result["eventType"] == "meeting.intelligence.generated"
    assert len(result["transcriptChunks"]) > 0
