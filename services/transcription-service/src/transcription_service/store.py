from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable

from shared.ids import new_id


@dataclass(slots=True)
class InMemoryMetadataStore:
    records: list[dict] = field(default_factory=list)

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
    ) -> None:
        self.records.append(
            {
                "tenantId": tenant_id,
                "meetingId": meeting_id,
                "videoItemId": video_item_id,
                "transcriptBucket": transcript_bucket,
                "transcriptKey": transcript_key,
                "languageCode": language_code,
                "speakerDiarization": speaker_diarization,
                "piiRedaction": pii_redaction,
                "transcriptionStatus": "completed",
            }
        )


class AuroraTranscriptionStore:
    def __init__(self, dsn: str | None = None, connection_factory: Callable[[], object] | None = None) -> None:
        self._dsn = dsn or os.getenv("AURORA_DATABASE_URL") or os.getenv("DATABASE_URL")
        if not self._dsn and connection_factory is None:
            raise ValueError("AURORA_DATABASE_URL or DATABASE_URL is required for AuroraTranscriptionStore.")
        self._connection_factory = connection_factory

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
    ) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO transcripts (
                        id, meeting_id, video_item_id, tenant_id, language_code,
                        transcript_s3_key, speaker_count, confidence_score, redaction_applied
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        new_id("trn"),
                        meeting_id,
                        video_item_id,
                        tenant_id,
                        language_code,
                        transcript_key,
                        2 if speaker_diarization else None,
                        0.95,
                        pii_redaction,
                    ),
                )
                cursor.execute(
                    """
                    UPDATE video_items
                    SET
                        transcript_s3_key = %s,
                        transcription_status = %s,
                        updated_at = NOW()
                    WHERE id = %s AND tenant_id = %s AND meeting_id = %s
                    """,
                    (
                        transcript_key,
                        "completed",
                        video_item_id,
                        tenant_id,
                        meeting_id,
                    ),
                )
            connection.commit()

    def _connect(self):
        if self._connection_factory is not None:
            return self._connection_factory()

        import psycopg

        return psycopg.connect(self._dsn)
