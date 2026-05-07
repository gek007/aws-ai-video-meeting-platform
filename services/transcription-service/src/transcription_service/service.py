from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from contracts.validation import require_keys
from shared.events import base_event
from transcription_service.transcriber import TranscriptionArtifact


class QueuePublisher(Protocol):
    def publish_ai_enrichment(self, payload: dict) -> None: ...


class Transcriber(Protocol):
    def transcribe(
        self,
        *,
        tenant_id: str,
        meeting_id: str,
        video_item_id: str,
        audio_bucket: str,
        audio_key: str,
        transcript_bucket: str,
        language_code: str,
        speaker_diarization: bool,
        pii_redaction: bool,
    ) -> TranscriptionArtifact: ...


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
        speaker_count: int | None,
        confidence_score: float | None,
    ) -> None: ...


@dataclass(slots=True)
class TranscriptionResult:
    next_event: dict


class TranscriptionService:
    def __init__(self, publisher: QueuePublisher, metadata_store: MetadataStore, transcriber: Transcriber) -> None:
        self._publisher = publisher
        self._metadata_store = metadata_store
        self._transcriber = transcriber

    def transcribe(self, event: dict) -> TranscriptionResult:
        require_keys(event, ["audio", "tenantId", "meetingId", "videoItemId", "correlationId"])
        audio = event["audio"]
        transcript_bucket = event.get("transcriptOutputBucket", "transcript-bucket")
        language_code = event.get("languageCode", "en-US")
        speaker_diarization = event.get("speakerDiarization", True)
        pii_redaction = event.get("piiRedaction", False)
        artifact = self._transcriber.transcribe(
            tenant_id=event["tenantId"],
            meeting_id=event["meetingId"],
            video_item_id=event["videoItemId"],
            audio_bucket=audio["bucket"],
            audio_key=audio["key"],
            transcript_bucket=transcript_bucket,
            language_code=language_code,
            speaker_diarization=speaker_diarization,
            pii_redaction=pii_redaction,
        )
        if not artifact.is_ready:
            next_event = base_event(
                "transcription.job.started",
                tenant_id=event["tenantId"],
                meeting_id=event["meetingId"],
                video_item_id=event["videoItemId"],
                correlation_id=event["correlationId"],
            )
            next_event["transcriptionProvider"] = artifact.provider
            next_event["transcriptionJobName"] = artifact.job_name
            next_event["expectedTranscript"] = {
                "bucket": artifact.transcript_bucket,
                "key": artifact.transcript_key,
                "language": artifact.language_code,
                "speakerDiarization": artifact.speaker_diarization,
                "piiRedaction": artifact.pii_redaction,
            }
            return TranscriptionResult(next_event=next_event)

        next_event = base_event(
            "meeting.transcript.ready",
            tenant_id=event["tenantId"],
            meeting_id=event["meetingId"],
            video_item_id=event["videoItemId"],
            correlation_id=event["correlationId"],
        )
        next_event["transcript"] = {
            "bucket": artifact.transcript_bucket,
            "key": artifact.transcript_key,
            "language": artifact.language_code,
            "speakerDiarization": artifact.speaker_diarization,
            "piiRedaction": artifact.pii_redaction,
        }
        next_event["transcriptionProvider"] = artifact.provider
        next_event["transcriptionJobName"] = artifact.job_name
        self._metadata_store.record_transcript(
            tenant_id=event["tenantId"],
            meeting_id=event["meetingId"],
            video_item_id=event["videoItemId"],
            transcript_bucket=artifact.transcript_bucket,
            transcript_key=artifact.transcript_key,
            language_code=artifact.language_code,
            speaker_diarization=artifact.speaker_diarization,
            pii_redaction=artifact.pii_redaction,
            speaker_count=artifact.speaker_count,
            confidence_score=artifact.confidence_score,
        )
        self._publisher.publish_ai_enrichment(next_event)
        return TranscriptionResult(next_event=next_event)


class TranscriptionCompletionService:
    def __init__(self, publisher: QueuePublisher, metadata_store: MetadataStore) -> None:
        self._publisher = publisher
        self._metadata_store = metadata_store

    def complete(self, event: dict) -> TranscriptionResult:
        detail = event.get("detail", {})
        status = event.get("transcriptionJobStatus") or detail.get("TranscriptionJobStatus")
        job_name = event.get("transcriptionJobName") or detail.get("TranscriptionJobName")
        if not job_name:
            raise ValueError("transcriptionJobName or detail.TranscriptionJobName is required.")

        ids = self._resolve_ids(event, job_name)
        if status != "COMPLETED":
            next_event = base_event(
                "transcription.job.failed",
                tenant_id=ids["tenantId"],
                meeting_id=ids["meetingId"],
                video_item_id=ids["videoItemId"],
                correlation_id=ids["correlationId"],
            )
            next_event["transcriptionProvider"] = event.get("transcriptionProvider", "amazon-transcribe")
            next_event["transcriptionJobName"] = job_name
            next_event["status"] = status or "UNKNOWN"
            return TranscriptionResult(next_event=next_event)

        transcript = self._resolve_transcript(event, ids)
        next_event = base_event(
            "meeting.transcript.ready",
            tenant_id=ids["tenantId"],
            meeting_id=ids["meetingId"],
            video_item_id=ids["videoItemId"],
            correlation_id=ids["correlationId"],
        )
        next_event["transcript"] = transcript
        next_event["transcriptionProvider"] = event.get("transcriptionProvider", "amazon-transcribe")
        next_event["transcriptionJobName"] = job_name
        self._metadata_store.record_transcript(
            tenant_id=ids["tenantId"],
            meeting_id=ids["meetingId"],
            video_item_id=ids["videoItemId"],
            transcript_bucket=transcript["bucket"],
            transcript_key=transcript["key"],
            language_code=transcript["language"],
            speaker_diarization=transcript["speakerDiarization"],
            pii_redaction=transcript["piiRedaction"],
            speaker_count=transcript.get("speakerCount"),
            confidence_score=transcript.get("confidenceScore"),
        )
        self._publisher.publish_ai_enrichment(next_event)
        return TranscriptionResult(next_event=next_event)

    def _resolve_ids(self, event: dict, job_name: str) -> dict:
        if {"tenantId", "meetingId", "videoItemId"}.issubset(event):
            return {
                "tenantId": event["tenantId"],
                "meetingId": event["meetingId"],
                "videoItemId": event["videoItemId"],
                "correlationId": event.get("correlationId"),
            }

        parts = job_name.split("__")
        if len(parts) != 4 or parts[0] != "transcribe":
            raise ValueError("Transcription job name must use transcribe__tenantId__meetingId__videoItemId.")
        return {
            "tenantId": parts[1],
            "meetingId": parts[2],
            "videoItemId": parts[3],
            "correlationId": event.get("correlationId"),
        }

    def _resolve_transcript(self, event: dict, ids: dict) -> dict:
        transcript = event.get("transcript", {})
        return {
            "bucket": transcript.get("bucket") or event.get("transcriptOutputBucket", "transcript-bucket"),
            "key": transcript.get("key") or f'{ids["tenantId"]}/{ids["meetingId"]}/{ids["videoItemId"]}/transcript.json',
            "language": transcript.get("language") or event.get("languageCode", "en-US"),
            "speakerDiarization": transcript.get("speakerDiarization", event.get("speakerDiarization", True)),
            "piiRedaction": transcript.get("piiRedaction", event.get("piiRedaction", False)),
        }
