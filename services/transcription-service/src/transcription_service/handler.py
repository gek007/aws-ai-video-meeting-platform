from __future__ import annotations

import os

from transcription_service.publisher import InMemoryQueuePublisher, SQSQueuePublisher
from transcription_service.store import AuroraTranscriptionStore, InMemoryMetadataStore
from shared.responses import json_response
from transcription_service.service import TranscriptionService


def lambda_handler(event: dict, _context) -> dict:
    publisher = _build_publisher()
    metadata_store = _build_metadata_store()
    result = TranscriptionService(publisher=publisher, metadata_store=metadata_store).transcribe(event)
    return json_response(202, {"message": "Transcript ready.", "nextEvent": result.next_event})


def _build_publisher():
    if os.getenv("AI_ENRICHMENT_QUEUE_URL"):
        return SQSQueuePublisher()
    return InMemoryQueuePublisher()


def _build_metadata_store():
    if os.getenv("AURORA_DATABASE_URL") or os.getenv("DATABASE_URL"):
        return AuroraTranscriptionStore()
    return InMemoryMetadataStore()
