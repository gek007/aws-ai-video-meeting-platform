from ai_enrichment_service.publisher import InMemoryTopicPublisher
from ai_enrichment_service.service import AIEnrichmentService


def test_ai_enrichment_service_returns_summary_topics_and_action_items():
    publisher = InMemoryTopicPublisher()
    result = AIEnrichmentService(publisher=publisher).enrich(
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
    assert publisher.messages[0]["eventType"] == "meeting.intelligence.generated"
