from __future__ import annotations

import os

from transcription_service.publisher import InMemoryQueuePublisher, SQSQueuePublisher
from transcription_service.store import AuroraTranscriptionStore, InMemoryMetadataStore
from transcription_service.transcriber import AmazonTranscribeClient, InMemoryTranscriber
from shared.responses import json_response
from transcription_service.service import TranscriptionCompletionService, TranscriptionService


def lambda_handler(event: dict, _context) -> dict:
    publisher = _build_publisher()
    metadata_store = _build_metadata_store()
    if _is_completion_event(event):
        result = TranscriptionCompletionService(
            publisher=publisher,
            metadata_store=metadata_store,
        ).complete(event)
        return json_response(202, {"message": "Transcription completion processed.", "nextEvent": result.next_event})

    transcriber = _build_transcriber()
    result = TranscriptionService(
        publisher=publisher,
        metadata_store=metadata_store,
        transcriber=transcriber,
    ).transcribe(event)
    return json_response(202, {"message": "Transcription processed.", "nextEvent": result.next_event})


def _build_publisher():
    if os.getenv("AI_ENRICHMENT_QUEUE_URL"):
        return SQSQueuePublisher()
    return InMemoryQueuePublisher()


def _build_metadata_store():
    if os.getenv("AURORA_DATABASE_URL") or os.getenv("DATABASE_URL"):
        return AuroraTranscriptionStore()
    return InMemoryMetadataStore()


def _build_transcriber():
    if os.getenv("TRANSCRIBE_OUTPUT_BUCKET"):
        return AmazonTranscribeClient()
    return InMemoryTranscriber()


def _is_completion_event(event: dict) -> bool:
    detail = event.get("detail", {})
    return "transcriptionJobStatus" in event or "TranscriptionJobStatus" in detail
