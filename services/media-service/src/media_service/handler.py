from __future__ import annotations

import os

from media_service.converter import FFmpegSubprocessConverter, InMemoryConverter, MediaConvertAdapter
from media_service.publisher import InMemoryQueuePublisher, SQSQueuePublisher
from media_service.service import MediaConversionCompletionService, MediaService
from media_service.store import AuroraMediaStore, InMemoryMetadataStore
from shared.responses import json_response


def lambda_handler(event: dict, _context) -> dict:
    event_type = event.get("eventType", "")

    if event_type == "media.conversion.job.completed" or "detail" in event and event.get("source") == "aws.mediaconvert":
        return _handle_completion(event)

    return _handle_processing(event)


def _handle_processing(event: dict) -> dict:
    publisher = _build_publisher()
    metadata_store = _build_metadata_store()
    converter = _build_converter()
    result = MediaService(
        publisher=publisher,
        metadata_store=metadata_store,
        converter=converter,
    ).process(event)
    return json_response(202, {"message": "Media processing started.", "nextEvent": result.next_event})


def _handle_completion(event: dict) -> dict:
    publisher = _build_publisher()
    metadata_store = _build_metadata_store()
    result = MediaConversionCompletionService(
        publisher=publisher,
        metadata_store=metadata_store,
    ).complete(event)
    return json_response(202, {"message": "Media conversion completed.", "nextEvent": result.next_event})


def _build_publisher():
    if os.getenv("TRANSCRIPTION_QUEUE_URL"):
        return SQSQueuePublisher()
    return InMemoryQueuePublisher()


def _build_metadata_store():
    if os.getenv("AURORA_DATABASE_URL") or os.getenv("DATABASE_URL"):
        return AuroraMediaStore()
    return InMemoryMetadataStore()


def _build_converter():
    engine = os.getenv("CONVERSION_ENGINE", "").lower()
    if engine == "ffmpeg":
        return FFmpegSubprocessConverter()
    if engine == "mediaconvert" and os.getenv("MEDIACONVERT_ROLE_ARN"):
        return MediaConvertAdapter()
    return InMemoryConverter()
