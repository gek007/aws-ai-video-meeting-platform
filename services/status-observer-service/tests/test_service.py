from dataclasses import dataclass, field

from status_observer_service.poller import ExternalTaskStatus, InMemoryStatusPoller
from status_observer_service.service import StatusObserverService
from status_observer_service.store import InMemoryMetadataStore


def test_status_observer_service_syncs_and_stores():
    metadata_store = InMemoryMetadataStore()
    result = StatusObserverService(metadata_store=metadata_store).sync(
        {"tenantId": "tenant_1", "provider": "jira", "externalId": "JIRA-001", "status": "DONE"}
    )

    assert result["tenantId"] == "tenant_1"
    assert result["status"] == "DONE"
    assert metadata_store.records[0]["status"] == "DONE"


def test_status_observer_emits_changed_when_status_differs():
    metadata_store = InMemoryMetadataStore()
    # seed an existing status
    metadata_store.record_task_status(tenant_id="tenant_1", provider="jira", external_id="JIRA-001", status="IN_PROGRESS")

    result = StatusObserverService(metadata_store=metadata_store).sync(
        {"tenantId": "tenant_1", "provider": "jira", "externalId": "JIRA-001", "status": "DONE"}
    )

    assert result["eventType"] == "task.status.changed"
    assert result["statusChanged"] is True
    assert result["previousStatus"] == "IN_PROGRESS"
    assert result["status"] == "DONE"


def test_status_observer_emits_synced_when_status_same():
    metadata_store = InMemoryMetadataStore()
    metadata_store.record_task_status(tenant_id="tenant_1", provider="jira", external_id="JIRA-001", status="DONE")

    result = StatusObserverService(metadata_store=metadata_store).sync(
        {"tenantId": "tenant_1", "provider": "jira", "externalId": "JIRA-001", "status": "DONE"}
    )

    assert result["eventType"] == "task.status.synced"
    assert result["statusChanged"] is False


def test_status_observer_uses_real_poller_when_provided():
    metadata_store = InMemoryMetadataStore()
    poller = InMemoryStatusPoller(status_map={"JIRA-123": "DONE"})
    metadata_store.record_task_status(tenant_id="tenant_1", provider="jira", external_id="JIRA-123", status="OPEN")

    result = StatusObserverService(metadata_store=metadata_store, poller=poller).sync(
        {"tenantId": "tenant_1", "provider": "jira", "externalId": "JIRA-123"}
    )

    assert result["status"] == "DONE"
    assert result["statusChanged"] is True
    assert result["eventType"] == "task.status.changed"


def test_status_observer_publishes_notification_on_change():
    @dataclass
    class _Publisher:
        published: list[dict] = field(default_factory=list)

        def publish_status_change(self, payload: dict) -> None:
            self.published.append(payload)

    metadata_store = InMemoryMetadataStore()
    metadata_store.record_task_status(tenant_id="t", provider="jira", external_id="J-1", status="OPEN")
    publisher = _Publisher()

    StatusObserverService(
        metadata_store=metadata_store,
        notification_publisher=publisher,
    ).sync({"tenantId": "t", "provider": "jira", "externalId": "J-1", "status": "DONE"})

    assert len(publisher.published) == 1
    assert publisher.published[0]["eventType"] == "task.status.changed"


def test_status_observer_does_not_publish_when_status_unchanged():
    @dataclass
    class _Publisher:
        published: list[dict] = field(default_factory=list)

        def publish_status_change(self, payload: dict) -> None:
            self.published.append(payload)

    metadata_store = InMemoryMetadataStore()
    metadata_store.record_task_status(tenant_id="t", provider="jira", external_id="J-1", status="DONE")
    publisher = _Publisher()

    StatusObserverService(
        metadata_store=metadata_store,
        notification_publisher=publisher,
    ).sync({"tenantId": "t", "provider": "jira", "externalId": "J-1", "status": "DONE"})

    assert len(publisher.published) == 0
