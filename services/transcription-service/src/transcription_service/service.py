from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from shared.events import base_event


class QueuePublisher(Protocol):
    def publish_ai_enrichment(self, payload: dict) -> None: ...


@dataclass(slots=True)
class TranscriptionResult:
    next_event: dict


class TranscriptionService:
    def __init__(self, publisher: QueuePublisher) -> None:
        self._publisher = publisher

    def transcribe(self, event: dict) -> TranscriptionResult:
        transcript_bucket = event.get("transcriptOutputBucket", "transcript-bucket")
        transcript_key = f'{event["tenantId"]}/{event["meetingId"]}/{event["videoItemId"]}/transcript.json'
        next_event = base_event(
            "meeting.transcript.ready",
            tenant_id=event["tenantId"],
            meeting_id=event["meetingId"],
            video_item_id=event["videoItemId"],
            correlation_id=event["correlationId"],
        )
        next_event["transcript"] = {
            "bucket": transcript_bucket,
            "key": transcript_key,
            "language": "en-US",
            "speakerDiarization": event.get("speakerDiarization", True),
            "piiRedaction": event.get("piiRedaction", False),
        }
        self._publisher.publish_ai_enrichment(next_event)
        return TranscriptionResult(next_event=next_event)
