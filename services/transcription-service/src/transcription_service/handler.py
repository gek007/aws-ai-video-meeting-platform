from __future__ import annotations

import os

from shared.responses import json_response
from transcription_service.publisher import InMemoryQueuePublisher, SQSQueuePublisher
from shared.responses import json_response
from transcription_service.service import TranscriptionService


def lambda_handler(event: dict, _context) -> dict:
    publisher = _build_publisher()
    result = TranscriptionService(publisher=publisher).transcribe(event)
    return json_response(202, {"message": "Transcript ready.", "nextEvent": result.next_event})


def _build_publisher():
    if os.getenv("AI_ENRICHMENT_QUEUE_URL"):
        return SQSQueuePublisher()
    return InMemoryQueuePublisher()
