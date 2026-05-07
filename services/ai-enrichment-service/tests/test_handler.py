import json
import os

from ai_enrichment_service.handler import lambda_handler


def test_ai_handler_returns_meeting_intelligence_event():
    os.environ["AI_ENRICHMENT_STUB"] = "true"
    try:
        response = lambda_handler(
            {
                "tenantId": "tenant_123",
                "meetingId": "mtg_123",
                "videoItemId": "vid_123",
                "correlationId": "corr_123",
            },
            None,
        )
        body = json.loads(response["body"])
        assert body["snsEvent"]["eventType"] == "meeting.intelligence.generated"
    finally:
        del os.environ["AI_ENRICHMENT_STUB"]
