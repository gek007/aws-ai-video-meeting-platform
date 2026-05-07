from __future__ import annotations

import os

from ingestion_service.publisher import InMemoryQueuePublisher, SQSQueuePublisher
from ingestion_service.service import IngestionService
from ingestion_service.store import AuroraMetadataStore, InMemoryMetadataStore
from shared.responses import json_response


def lambda_handler(event: dict, _context) -> dict:
    metadata_store = _build_metadata_store()
    publisher = _build_publisher()
    service = IngestionService(metadata_store=metadata_store, publisher=publisher)

    result = service.ingest_s3_event(event["detail"])

    return json_response(
        202,
        {
            "message": "Video accepted for processing.",
            "meetingId": result.meeting_id,
            "videoItemId": result.video_item_id,
            "processingJobId": result.processing_job_id,
            "nextEvent": result.next_event,
        },
    )


def _build_publisher():
    if os.getenv("MEDIA_PROCESSING_QUEUE_URL"):
        return SQSQueuePublisher()
    return InMemoryQueuePublisher()


def _build_metadata_store():
    if os.getenv("AURORA_DATABASE_URL") or os.getenv("DATABASE_URL"):
        return AuroraMetadataStore()
    return InMemoryMetadataStore()
