from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime


@dataclass(slots=True)
class RawVideoLocation:
    bucket: str
    key: str


@dataclass(slots=True)
class MeetingUploadedEvent:
    event_type: str
    event_version: str
    event_id: str
    occurred_at: str
    tenant_id: str
    meeting_id: str
    video_item_id: str
    source: str
    raw_video: RawVideoLocation
    correlation_id: str
    idempotency_key: str

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["eventType"] = payload.pop("event_type")
        payload["eventVersion"] = payload.pop("event_version")
        payload["eventId"] = payload.pop("event_id")
        payload["occurredAt"] = payload.pop("occurred_at")
        payload["tenantId"] = payload.pop("tenant_id")
        payload["meetingId"] = payload.pop("meeting_id")
        payload["videoItemId"] = payload.pop("video_item_id")
        payload["rawVideo"] = payload.pop("raw_video")
        payload["correlationId"] = payload.pop("correlation_id")
        payload["idempotencyKey"] = payload.pop("idempotency_key")
        return payload


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()

