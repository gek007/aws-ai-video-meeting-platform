from __future__ import annotations

from dataclasses import dataclass, field

from shared.aurora import AuroraBaseStore


@dataclass(slots=True)
class InMemoryMetadataStore:
    updates: list[dict] = field(default_factory=list)

    def record_audio_artifact(
        self,
        *,
        tenant_id: str,
        meeting_id: str,
        video_item_id: str,
        audio_bucket: str,
        audio_key: str,
        conversion_engine: str,
    ) -> None:
        self.updates.append(
            {
                "tenantId": tenant_id,
                "meetingId": meeting_id,
                "videoItemId": video_item_id,
                "audioBucket": audio_bucket,
                "audioKey": audio_key,
                "conversionEngine": conversion_engine,
                "processingStatus": "completed",
            }
        )


class AuroraMediaStore(AuroraBaseStore):
    def __init__(self, dsn: str | None = None, connection_factory=None) -> None:
        super().__init__(dsn, connection_factory, store_name="AuroraMediaStore")

    def record_audio_artifact(
        self,
        *,
        tenant_id: str,
        meeting_id: str,
        video_item_id: str,
        audio_bucket: str,
        audio_key: str,
        conversion_engine: str,
    ) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE video_items
                    SET
                        audio_s3_key = %s,
                        audio_codec = %s,
                        processing_status = %s,
                        updated_at = NOW()
                    WHERE id = %s AND tenant_id = %s AND meeting_id = %s
                    """,
                    (
                        audio_key,
                        "wav",
                        "completed",
                        video_item_id,
                        tenant_id,
                        meeting_id,
                    ),
                )
            connection.commit()

