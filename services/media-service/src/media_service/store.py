from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable


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


class AuroraMediaStore:
    def __init__(self, dsn: str | None = None, connection_factory: Callable[[], object] | None = None) -> None:
        self._dsn = dsn or os.getenv("AURORA_DATABASE_URL") or os.getenv("DATABASE_URL")
        if not self._dsn and connection_factory is None:
            raise ValueError("AURORA_DATABASE_URL or DATABASE_URL is required for AuroraMediaStore.")
        self._connection_factory = connection_factory

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

    def _connect(self):
        if self._connection_factory is not None:
            return self._connection_factory()

        import psycopg

        return psycopg.connect(self._dsn)
