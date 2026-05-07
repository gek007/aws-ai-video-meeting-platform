from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable

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


class AuroraIntegrationStore:
    def __init__(self, dsn: str | None = None, connection_factory: Callable[[], object] | None = None) -> None:
        self._dsn = dsn or os.getenv("AURORA_DATABASE_URL") or os.getenv("DATABASE_URL")
        if not self._dsn and connection_factory is None:
            raise ValueError("AURORA_DATABASE_URL or DATABASE_URL is required for AuroraIntegrationStore.")
        self._connection_factory = connection_factory

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

    def _connect(self):
        if self._connection_factory is not None:
            return self._connection_factory()

        import psycopg

        return psycopg.connect(self._dsn)
