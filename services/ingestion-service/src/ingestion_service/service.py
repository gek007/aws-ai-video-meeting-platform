from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from contracts.events import MeetingUploadedEvent, RawVideoLocation, utc_now_iso
from contracts.validation import require_keys
from shared.idempotency import IdempotencyStore
from shared.ids import new_id


class MetadataStore(Protocol):
    def create_initial_records(self, event: MeetingUploadedEvent, processing_job_id: str) -> None: ...


class QueuePublisher(Protocol):
    def publish_media_processing(self, payload: dict) -> None: ...


@dataclass(slots=True)
class IngestionResult:
    meeting_id: str
    video_item_id: str
    processing_job_id: str
    next_event: dict


class IngestionService:
    def __init__(self, metadata_store: MetadataStore, publisher: QueuePublisher, idempotency_store: IdempotencyStore | None = None) -> None:
        self._metadata_store = metadata_store
        self._publisher = publisher
        self._idempotency_store = idempotency_store or IdempotencyStore()

    def ingest_uploaded_video(self, *, bucket: str, key: str, tenant_id: str, source: str) -> IngestionResult:
        meeting_id = new_id("mtg")
        video_item_id = new_id("vid")
        processing_job_id = new_id("job")
        correlation_id = new_id("corr")

        event = MeetingUploadedEvent(
            event_type="meeting.uploaded",
            event_version="1.0",
            event_id=new_id("evt"),
            occurred_at=utc_now_iso(),
            tenant_id=tenant_id,
            meeting_id=meeting_id,
            video_item_id=video_item_id,
            source=source,
            raw_video=RawVideoLocation(bucket=bucket, key=key),
            correlation_id=correlation_id,
            idempotency_key=f"{tenant_id}:{bucket}:{key}:meeting.uploaded",
        )
        if self._idempotency_store.seen(event.idempotency_key):
            return IngestionResult(
                meeting_id=meeting_id,
                video_item_id=video_item_id,
                processing_job_id=processing_job_id,
                next_event={"eventType": "media.processing.requested", "deduplicated": True},
            )
        self._idempotency_store.remember(event.idempotency_key)

        self._metadata_store.create_initial_records(event, processing_job_id)

        next_event = {
            "eventType": "media.processing.requested",
            "eventVersion": "1.0",
            "tenantId": tenant_id,
            "meetingId": meeting_id,
            "videoItemId": video_item_id,
            "processingJobId": processing_job_id,
            "rawVideo": {
                "bucket": bucket,
                "key": key,
            },
            "correlationId": correlation_id,
        }
        self._publisher.publish_media_processing(next_event)

        return IngestionResult(
            meeting_id=meeting_id,
            video_item_id=video_item_id,
            processing_job_id=processing_job_id,
            next_event=next_event,
        )

    def ingest_s3_event(self, detail: dict) -> IngestionResult:
        require_keys(detail, ["bucket", "object"])
        return self.ingest_uploaded_video(
            bucket=detail["bucket"]["name"],
            key=detail["object"]["key"],
            tenant_id=detail.get("tenantId", "tenant_default"),
            source=detail.get("source", "manual_upload"),
        )
