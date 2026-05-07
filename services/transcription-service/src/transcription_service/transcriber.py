from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True, slots=True)
class TranscriptionArtifact:
    transcript_bucket: str
    transcript_key: str
    language_code: str
    speaker_diarization: bool
    pii_redaction: bool
    job_name: str
    provider: str
    is_ready: bool
    speaker_count: int | None = None
    confidence_score: float | None = None


class InMemoryTranscriber:
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
    ) -> TranscriptionArtifact:
        return TranscriptionArtifact(
            transcript_bucket=transcript_bucket,
            transcript_key=f"{tenant_id}/{meeting_id}/{video_item_id}/transcript.json",
            language_code=language_code,
            speaker_diarization=speaker_diarization,
            pii_redaction=pii_redaction,
            job_name=f"transcribe-{video_item_id}",
            provider="in-memory",
            is_ready=True,
        )


class AmazonTranscribeClient:
    def __init__(
        self,
        output_bucket: str | None = None,
        client_factory: Callable[[], object] | None = None,
    ) -> None:
        self._output_bucket = output_bucket or os.getenv("TRANSCRIBE_OUTPUT_BUCKET")
        if not self._output_bucket:
            raise ValueError("TRANSCRIBE_OUTPUT_BUCKET is required for AmazonTranscribeClient.")
        self._client_factory = client_factory
        self._cached_client: object | None = None

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
    ) -> TranscriptionArtifact:
        del transcript_bucket

        job_name = f"transcribe__{tenant_id}__{meeting_id}__{video_item_id}"
        transcript_key = f"{tenant_id}/{meeting_id}/{video_item_id}/transcript.json"
        settings = {}
        content_redaction = None

        if speaker_diarization:
            settings["ShowSpeakerLabels"] = True
            settings["MaxSpeakerLabels"] = 10
        if pii_redaction:
            content_redaction = {
                "RedactionType": "PII",
                "RedactionOutput": "redacted",
            }

        request = {
            "TranscriptionJobName": job_name,
            "Media": {"MediaFileUri": f"s3://{audio_bucket}/{audio_key}"},
            "MediaFormat": audio_key.rsplit(".", 1)[-1],
            "LanguageCode": language_code,
            "OutputBucketName": self._output_bucket,
            "OutputKey": transcript_key,
        }
        if settings:
            request["Settings"] = settings
        if content_redaction is not None:
            request["ContentRedaction"] = content_redaction

        self._client.start_transcription_job(**request)
        return TranscriptionArtifact(
            transcript_bucket=self._output_bucket,
            transcript_key=transcript_key,
            language_code=language_code,
            speaker_diarization=speaker_diarization,
            pii_redaction=pii_redaction,
            job_name=job_name,
            provider="amazon-transcribe",
            is_ready=False,
        )

    @property
    def _client(self):
        if self._cached_client is None:
            if self._client_factory is not None:
                self._cached_client = self._client_factory()
            else:
                import boto3

                self._cached_client = boto3.client("transcribe")
        return self._cached_client
