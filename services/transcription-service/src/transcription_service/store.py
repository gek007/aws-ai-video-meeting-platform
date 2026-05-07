from __future__ import annotations

from dataclasses import dataclass, field

from shared.aurora import AuroraBaseStore
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
        speaker_count: int | None = None,
        confidence_score: float | None = None,
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
                "speakerCount": speaker_count,
                "confidenceScore": confidence_score,
                "transcriptionStatus": "completed",
            }
        )


class AuroraTranscriptionStore(AuroraBaseStore):
    def __init__(self, dsn: str | None = None, connection_factory=None) -> None:
        super().__init__(dsn, connection_factory, store_name="AuroraTranscriptionStore")

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
        speaker_count: int | None = None,
        confidence_score: float | None = None,
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
                        speaker_count,
                        confidence_score,
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

