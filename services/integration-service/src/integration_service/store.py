from __future__ import annotations

from dataclasses import dataclass, field

from shared.aurora import AuroraBaseStore
from shared.ids import new_id


@dataclass(slots=True)
class InMemoryMetadataStore:
    records: list[dict] = field(default_factory=list)

    def record_external_task(
        self,
        *,
        tenant_id: str,
        action_item_id: str,
        provider: str,
        external_id: str,
        external_url: str,
        status: str,
    ) -> None:
        self.records.append(
            {
                "tenantId": tenant_id,
                "actionItemId": action_item_id,
                "provider": provider,
                "externalId": external_id,
                "externalUrl": external_url,
                "status": status,
            }
        )


class AuroraIntegrationStore(AuroraBaseStore):
    def __init__(self, dsn: str | None = None, connection_factory=None) -> None:
        super().__init__(dsn, connection_factory, store_name="AuroraIntegrationStore")

    def record_external_task(
        self,
        *,
        tenant_id: str,
        action_item_id: str,
        provider: str,
        external_id: str,
        external_url: str,
        status: str,
    ) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO external_tasks (
                        id, action_item_id, tenant_id, provider, external_id,
                        external_url, external_status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        new_id("ext"),
                        action_item_id,
                        tenant_id,
                        provider,
                        external_id,
                        external_url,
                        status,
                    ),
                )
            connection.commit()

