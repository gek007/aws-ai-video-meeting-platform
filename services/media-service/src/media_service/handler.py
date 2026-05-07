from __future__ import annotations

import os

from media_service.publisher import InMemoryQueuePublisher, SQSQueuePublisher
from media_service.service import MediaService
from media_service.store import AuroraMediaStore, InMemoryMetadataStore
from shared.responses import json_response


def lambda_handler(event: dict, _context) -> dict:
    publisher = _build_publisher()
    metadata_store = _build_metadata_store()
    result = MediaService(publisher=publisher, metadata_store=metadata_store).process(event)
    return json_response(202, {"message": "Media processed.", "nextEvent": result.next_event})


def _build_publisher():
    if os.getenv("TRANSCRIPTION_QUEUE_URL"):
        return SQSQueuePublisher()
    return InMemoryQueuePublisher()


def _build_metadata_store():
    if os.getenv("AURORA_DATABASE_URL") or os.getenv("DATABASE_URL"):
        return AuroraMediaStore()
    return InMemoryMetadataStore()
