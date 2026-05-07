from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Callable

from contracts.events import MeetingUploadedEvent


@dataclass(slots=True)
class InMemoryMetadataStore:
    records: list[dict] = field(default_factory=list)

    def create_initial_records(self, event: MeetingUploadedEvent, processing_job_id: str) -> None:
        payload = event.to_dict()
        payload["processingJobId"] = processing_job_id
        self.records.append(payload)


class AuroraMetadataStore:
    def __init__(self, dsn: str | None = None, connection_factory: Callable[[], object] | None = None) -> None:
        self._dsn = dsn or os.getenv("AURORA_DATABASE_URL") or os.getenv("DATABASE_URL")
        if not self._dsn and connection_factory is None:
            raise ValueError("AURORA_DATABASE_URL or DATABASE_URL is required for AuroraMetadataStore.")
        self._connection_factory = connection_factory

    def create_initial_records(self, event: MeetingUploadedEvent, processing_job_id: str) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO meetings (id, tenant_id, source_type, title, status)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        event.meeting_id,
                        event.tenant_id,
                        event.source,
                        self._title_from_key(event.raw_video.key),
                        "pending",
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO video_items (
                        id, tenant_id, meeting_id, source_type, original_filename,
                        s3_bucket, s3_key, upload_status, processing_status,
                        transcription_status, ai_enrichment_status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        event.video_item_id,
                        event.tenant_id,
                        event.meeting_id,
                        event.source,
                        PurePosixPath(event.raw_video.key).name,
                        event.raw_video.bucket,
                        event.raw_video.key,
                        "uploaded",
                        "queued",
                        "pending",
                        "pending",
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO processing_jobs (
                        id, meeting_id, video_item_id, tenant_id, job_type, status, attempt_count
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        processing_job_id,
                        event.meeting_id,
                        event.video_item_id,
                        event.tenant_id,
                        "media-processing",
                        "queued",
                        0,
                    ),
                )
            connection.commit()

    def _connect(self):
        if self._connection_factory is not None:
            return self._connection_factory()

        import psycopg

        return psycopg.connect(self._dsn)

    @staticmethod
    def _title_from_key(key: str) -> str:
        stem = PurePosixPath(key).stem.replace("-", " ").replace("_", " ").strip()
        return stem.title() or "Uploaded Meeting"
