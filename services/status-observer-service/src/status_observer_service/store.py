from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable


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


class AuroraStatusObserverStore:
    def __init__(self, dsn: str | None = None, connection_factory: Callable[[], object] | None = None) -> None:
        self._dsn = dsn or os.getenv("AURORA_DATABASE_URL") or os.getenv("DATABASE_URL")
        if not self._dsn and connection_factory is None:
            raise ValueError("AURORA_DATABASE_URL or DATABASE_URL is required for AuroraStatusObserverStore.")
        self._connection_factory = connection_factory

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

    def _connect(self):
        if self._connection_factory is not None:
            return self._connection_factory()

        import psycopg

        return psycopg.connect(self._dsn)
