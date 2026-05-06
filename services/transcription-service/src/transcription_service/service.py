from __future__ import annotations

from shared.events import base_event


class TranscriptionService:
    def transcribe(self, event: dict) -> dict:
        next_event = base_event(
            "meeting.transcript.ready",
            tenant_id=event["tenantId"],
            meeting_id=event["meetingId"],
            video_item_id=event["videoItemId"],
            correlation_id=event["correlationId"],
        )
        next_event["transcript"] = {
            "bucket": "transcript-bucket",
            "key": f'{event["videoItemId"]}/transcript.json',
            "language": "en-US",
        }
        return next_event

