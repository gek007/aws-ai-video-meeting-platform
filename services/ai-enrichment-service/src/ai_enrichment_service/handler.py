from __future__ import annotations

import os

from ai_enrichment_service.publisher import InMemoryTopicPublisher, SNSTopicPublisher
from ai_enrichment_service.service import AIEnrichmentService
from shared.responses import json_response


def lambda_handler(event: dict, _context) -> dict:
    publisher = _build_publisher()
    result = AIEnrichmentService(publisher=publisher).enrich(event)
    return json_response(202, {"message": "Meeting intelligence generated.", "snsEvent": result})


def _build_publisher():
    if os.getenv("MEETING_INTELLIGENCE_TOPIC_ARN"):
        return SNSTopicPublisher()
    return InMemoryTopicPublisher()
