from ai_enrichment_service.publisher import InMemoryTopicPublisher
from ai_enrichment_service.store import InMemoryMetadataStore
from ai_enrichment_service.service import AIEnrichmentService


def test_ai_enrichment_chunks_transcript_and_sets_prompt_version():
    service = AIEnrichmentService(
        publisher=InMemoryTopicPublisher(),
        metadata_store=InMemoryMetadataStore(),
    )
    result = service.enrich(
        {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
            "correlationId": "corr_123",
            "transcriptText": "word " * 260,
        }
    )

    assert result["promptVersion"] == "v1"
    assert len(result["transcriptChunks"]) >= 3
    assert len(result["embeddings"]) == len(result["transcriptChunks"])
