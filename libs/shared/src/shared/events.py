from __future__ import annotations

from shared.ids import new_id


def base_event(event_type: str, tenant_id: str, meeting_id: str, video_item_id: str, correlation_id: str | None = None) -> dict:
    return {
        "eventType": event_type,
        "eventVersion": "1.0",
        "eventId": new_id("evt"),
        "tenantId": tenant_id,
        "meetingId": meeting_id,
        "videoItemId": video_item_id,
        "correlationId": correlation_id or new_id("corr"),
    }

