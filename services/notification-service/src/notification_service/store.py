from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable

from shared.ids import new_id


@dataclass(slots=True)
class InMemoryMetadataStore:
    records: list[dict] = field(default_factory=list)

    def record_notification(
        self,
        *,
        tenant_id: str,
        meeting_id: str | None,
        video_item_id: str | None,
        recipient: str,
        channel: str,
        template_name: str,
        status: str,
    ) -> None:
        self.records.append(
            {
                "tenantId": tenant_id,
                "meetingId": meeting_id,
                "videoItemId": video_item_id,
                "recipient": recipient,
                "channel": channel,
                "templateName": template_name,
                "status": status,
            }
        )


class AuroraNotificationStore:
    def __init__(self, dsn: str | None = None, connection_factory: Callable[[], object] | None = None) -> None:
        self._dsn = dsn or os.getenv("AURORA_DATABASE_URL") or os.getenv("DATABASE_URL")
        if not self._dsn and connection_factory is None:
            raise ValueError("AURORA_DATABASE_URL or DATABASE_URL is required for AuroraNotificationStore.")
        self._connection_factory = connection_factory

    def record_notification(
        self,
        *,
        tenant_id: str,
        meeting_id: str | None,
        video_item_id: str | None,
        recipient: str,
        channel: str,
        template_name: str,
        status: str,
    ) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO notifications (
                        id, tenant_id, meeting_id, video_item_id, recipient,
                        channel, template_name, status, sent_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (
                        new_id("ntf"),
                        tenant_id,
                        meeting_id,
                        video_item_id,
                        recipient,
                        channel,
                        template_name,
                        status,
                    ),
                )
            connection.commit()

    def _connect(self):
        if self._connection_factory is not None:
            return self._connection_factory()

        import psycopg

        return psycopg.connect(self._dsn)
