from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from shared.events import base_event


class QueuePublisher(Protocol):
    def publish_ai_enrichment(self, payload: dict) -> None: ...


class MetadataStore(Protocol):
    def record_transcript(
        self,
        *,
        tenant_id: str,
        meeting_id: str,
        video_item_id: str,
        transcript_bucket: str,
        transcript_key: str,
        language_code: str,
        speaker_diarization: bool,
        pii_redaction: bool,
    ) -> None: ...


@dataclass(slots=True)
class TranscriptionResult:
    next_event: dict


class TranscriptionService:
    def __init__(self, publisher: QueuePublisher, metadata_store: MetadataStore) -> None:
        self._publisher = publisher
        self._metadata_store = metadata_store

    def transcribe(self, event: dict) -> TranscriptionResult:
        transcript_bucket = event.get("transcriptOutputBucket", "transcript-bucket")
        transcript_key = f'{event["tenantId"]}/{event["meetingId"]}/{event["videoItemId"]}/transcript.json'
        language_code = event.get("languageCode", "en-US")
        speaker_diarization = event.get("speakerDiarization", True)
        pii_redaction = event.get("piiRedaction", False)
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
            "language": language_code,
            "speakerDiarization": speaker_diarization,
            "piiRedaction": pii_redaction,
        }
        self._metadata_store.record_transcript(
            tenant_id=event["tenantId"],
            meeting_id=event["meetingId"],
            video_item_id=event["videoItemId"],
            transcript_bucket=transcript_bucket,
            transcript_key=transcript_key,
            language_code=language_code,
            speaker_diarization=speaker_diarization,
            pii_redaction=pii_redaction,
        )
        self._publisher.publish_ai_enrichment(next_event)
        return TranscriptionResult(next_event=next_event)
