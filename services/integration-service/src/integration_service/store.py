from __future__ import annotations

from dataclasses import dataclass, field

from shared.aurora import AuroraBaseStore
from shared.ids import new_id


@dataclass(slots=True)
class InMemoryMetadataStore:
    records: list[dict] = field(default_factory=list)

    def find_existing_task(
        self,
        *,
        action_item_id: str,
        provider: str,
        provider_project_key: str,
    ) -> dict | None:
        for record in self.records:
            if (
                record["actionItemId"] == action_item_id
                and record["provider"] == provider
                and record.get("providerProjectKey", "") == provider_project_key
            ):
                return record
        return None

    def record_external_task(
        self,
        *,
        tenant_id: str,
        action_item_id: str,
        provider: str,
        provider_project_key: str,
        external_id: str,
        external_url: str,
        status: str,
    ) -> None:
        self.records.append(
            {
                "tenantId": tenant_id,
                "actionItemId": action_item_id,
                "provider": provider,
                "providerProjectKey": provider_project_key,
                "externalId": external_id,
                "externalUrl": external_url,
                "status": status,
            }
        )


class AuroraIntegrationStore(AuroraBaseStore):
    def __init__(self, dsn: str | None = None, connection_factory=None) -> None:
        super().__init__(dsn, connection_factory, store_name="AuroraIntegrationStore")

    def find_existing_task(
        self,
        *,
        action_item_id: str,
        provider: str,
        provider_project_key: str,
    ) -> dict | None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT external_id, external_url, external_status
                    FROM external_tasks
                    WHERE action_item_id = %s
                      AND provider = %s
                      AND provider_project_key = %s
                    LIMIT 1
                    """,
                    (action_item_id, provider, provider_project_key),
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "externalId": row[0],
                        "externalUrl": row[1],
                        "status": row[2],
                    }
                return None

    def record_external_task(
        self,
        *,
        tenant_id: str,
        action_item_id: str,
        provider: str,
        provider_project_key: str,
        external_id: str,
        external_url: str,
        status: str,
    ) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO external_tasks (
                        id, action_item_id, tenant_id, provider, provider_project_key,
                        external_id, external_url, external_status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (action_item_id, provider, provider_project_key) DO NOTHING
                    """,
                    (
                        new_id("ext"),
                        action_item_id,
                        tenant_id,
                        provider,
                        provider_project_key,
                        external_id,
                        external_url,
                        status,
                    ),
                )
            connection.commit()
