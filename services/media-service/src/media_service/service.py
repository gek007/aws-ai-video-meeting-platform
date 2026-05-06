from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from shared.events import base_event


class QueuePublisher(Protocol):
    def publish_transcription_request(self, payload: dict) -> None: ...


@dataclass(slots=True)
class MediaProcessingResult:
    next_event: dict


class MediaService:
    def __init__(self, publisher: QueuePublisher) -> None:
        self._publisher = publisher

    def process(self, event: dict) -> MediaProcessingResult:
        raw_video = event["rawVideo"]
        output_bucket = event.get("audioOutputBucket", "audio-bucket")
        output_key = f'{event["tenantId"]}/{event["meetingId"]}/{event["videoItemId"]}/audio.wav'

        next_event = base_event(
            "transcription.requested",
            tenant_id=event["tenantId"],
            meeting_id=event["meetingId"],
            video_item_id=event["videoItemId"],
            correlation_id=event["correlationId"],
        )
        next_event["sourceVideo"] = {
            "bucket": raw_video["bucket"],
            "key": raw_video["key"],
        }
        next_event["audio"] = {
            "bucket": output_bucket,
            "key": output_key,
            "format": "wav",
            "sampleRateHz": 16000,
            "channels": 1,
        }
        next_event["conversion"] = {
            "engine": event.get("conversionEngine", "mediaconvert"),
            "status": "completed",
            "targetProfile": "transcribe-optimized",
        }
        self._publisher.publish_transcription_request(next_event)
        return MediaProcessingResult(next_event=next_event)
