from __future__ import annotations

from dataclasses import dataclass, field

from shared.aurora import AuroraBaseStore
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


class AuroraNotificationStore(AuroraBaseStore):
    def __init__(self, dsn: str | None = None, connection_factory=None) -> None:
        super().__init__(dsn, connection_factory, store_name="AuroraNotificationStore")

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

