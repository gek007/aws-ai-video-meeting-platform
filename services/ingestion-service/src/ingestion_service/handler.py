from __future__ import annotations

import os
from dataclasses import dataclass, field

from ingestion_service.publisher import InMemoryQueuePublisher, SQSQueuePublisher
from ingestion_service.service import IngestionService
from shared.responses import json_response


@dataclass(slots=True)
class InMemoryMetadataStore:
    records: list[dict] = field(default_factory=list)

    def create_initial_records(self, event) -> None:
        self.records.append(event.to_dict())


def lambda_handler(event: dict, _context) -> dict:
    metadata_store = InMemoryMetadataStore()
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
