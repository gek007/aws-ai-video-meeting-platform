from __future__ import annotations

from typing import Protocol

from status_observer_service.poller import ExternalTaskStatus


class MetadataStore(Protocol):
    def record_task_status(
        self,
        *,
        tenant_id: str,
        provider: str,
        external_id: str,
        status: str,
    ) -> None: ...

    def get_task_status(
        self,
        *,
        tenant_id: str,
        provider: str,
        external_id: str,
    ) -> str | None: ...


class NotificationPublisher(Protocol):
    def publish_status_change(self, payload: dict) -> None: ...


class StatusPoller(Protocol):
    def poll(self, *, provider: str, external_id: str, config: dict) -> ExternalTaskStatus: ...


class StatusObserverService:
    def __init__(
        self,
        metadata_store: MetadataStore,
        poller: StatusPoller | None = None,
        notification_publisher: NotificationPublisher | None = None,
    ) -> None:
        self._metadata_store = metadata_store
        self._poller = poller
        self._notification_publisher = notification_publisher

    def sync(self, event: dict) -> dict:
        tenant_id = event.get("tenantId", "tenant_demo")
        provider = event.get("provider", "jira")
        external_id = event.get("externalId", "jira-001")
        provider_config = event.get("providerConfig", {})

        if self._poller is not None:
            fetched = self._poller.poll(
                provider=provider,
                external_id=external_id,
                config=provider_config,
            )
            new_status = fetched.status
        else:
            new_status = event.get("status", "OPEN")

        previous_status = self._metadata_store.get_task_status(
            tenant_id=tenant_id,
            provider=provider,
            external_id=external_id,
        )
        status_changed = previous_status is not None and previous_status != new_status

        self._metadata_store.record_task_status(
            tenant_id=tenant_id,
            provider=provider,
            external_id=external_id,
            status=new_status,
        )

        result = {
            "eventType": "task.status.changed" if status_changed else "task.status.synced",
            "tenantId": tenant_id,
            "provider": provider,
            "externalId": external_id,
            "status": new_status,
            "previousStatus": previous_status,
            "statusChanged": status_changed,
        }

        if status_changed and self._notification_publisher is not None:
            self._notification_publisher.publish_status_change(result)

        return result
