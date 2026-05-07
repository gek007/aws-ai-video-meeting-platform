from __future__ import annotations

from dataclasses import dataclass, field

from shared.aurora import AuroraBaseStore


@dataclass(slots=True)
class InMemoryMetadataStore:
    records: list[dict] = field(default_factory=list)

    def record_task_status(
        self,
        *,
        tenant_id: str,
        provider: str,
        external_id: str,
        status: str,
    ) -> None:
        self.records.append(
            {
                "tenantId": tenant_id,
                "provider": provider,
                "externalId": external_id,
                "status": status,
            }
        )


class AuroraStatusObserverStore(AuroraBaseStore):
    def __init__(self, dsn: str | None = None, connection_factory=None) -> None:
        super().__init__(dsn, connection_factory, store_name="AuroraStatusObserverStore")

    def record_task_status(
        self,
        *,
        tenant_id: str,
        provider: str,
        external_id: str,
        status: str,
    ) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE external_tasks
                    SET
                        external_status = %s,
                        last_synced_at = NOW(),
                        updated_at = NOW()
                    WHERE tenant_id = %s AND provider = %s AND external_id = %s
                    """,
                    (
                        status,
                        tenant_id,
                        provider,
                        external_id,
                    ),
                )
            connection.commit()

