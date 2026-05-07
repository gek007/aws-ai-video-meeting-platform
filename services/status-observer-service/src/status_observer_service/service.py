from __future__ import annotations

from typing import Protocol


class MetadataStore(Protocol):
    def record_task_status(
        self,
        *,
        tenant_id: str,
        provider: str,
        external_id: str,
        status: str,
    ) -> None: ...


class StatusObserverService:
    def __init__(self, metadata_store: MetadataStore) -> None:
        self._metadata_store = metadata_store

    def sync(self, event: dict) -> dict:
        result = {
            "eventType": "task.status.changed",
            "tenantId": event.get("tenantId", "tenant_demo"),
            "provider": event.get("provider", "jira"),
            "externalId": event.get("externalId", "jira-001"),
            "status": event.get("status", "DONE"),
        }
        self._metadata_store.record_task_status(
            tenant_id=result["tenantId"],
            provider=result["provider"],
            external_id=result["externalId"],
            status=result["status"],
        )
        return result
