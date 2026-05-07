from ai_enrichment_service.publisher import InMemoryTopicPublisher
from ai_enrichment_service.store import InMemoryMetadataStore
from ai_enrichment_service.service import AIEnrichmentService


def test_ai_enrichment_service_returns_summary_topics_and_action_items():
    publisher = InMemoryTopicPublisher()
    metadata_store = InMemoryMetadataStore()
    result = AIEnrichmentService(publisher=publisher, metadata_store=metadata_store).enrich(
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
    assert publisher.messages[0]["eventType"] == "meeting.intelligence.generated"
    assert metadata_store.records[0]["aiEnrichmentStatus"] == "completed"
