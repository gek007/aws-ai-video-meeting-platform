from __future__ import annotations

import os

from media_service.publisher import InMemoryQueuePublisher, SQSQueuePublisher
from media_service.service import MediaService
from shared.responses import json_response


def lambda_handler(event: dict, _context) -> dict:
    publisher = _build_publisher()
    result = MediaService(publisher=publisher).process(event)
    return json_response(202, {"message": "Media processed.", "nextEvent": result.next_event})


def _build_publisher():
    if os.getenv("TRANSCRIPTION_QUEUE_URL"):
        return SQSQueuePublisher()
    return InMemoryQueuePublisher()
