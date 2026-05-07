from status_observer_service.service import StatusObserverService
from status_observer_service.store import InMemoryMetadataStore


def test_status_observer_service_returns_default_done_status():
    metadata_store = InMemoryMetadataStore()
    result = StatusObserverService(metadata_store=metadata_store).sync({})

    assert result["eventType"] == "task.status.changed"
    assert result["tenantId"] == "tenant_demo"
    assert result["provider"] == "jira"
    assert result["status"] == "DONE"
    assert metadata_store.records[0]["tenantId"] == "tenant_demo"
    assert metadata_store.records[0]["externalId"] == "jira-001"
