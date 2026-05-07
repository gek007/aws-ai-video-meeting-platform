from integration_service.service import IntegrationService
from integration_service.store import InMemoryMetadataStore


def _event(action_item_id="act_123", provider="jira", project_key="PROJ"):
    return {
        "provider": provider,
        "providerProjectKey": project_key,
        "tenantId": "tenant_demo",
        "items": [{"actionItemId": action_item_id, "title": "Fix login timeout", "description": "Investigate issue"}],
    }


def test_integration_service_returns_external_task_metadata():
    metadata_store = InMemoryMetadataStore()
    result = IntegrationService(metadata_store=metadata_store).create_external_task(_event())

    assert result["eventType"] == "external.task.created"
    assert result["actionItemId"] == "act_123"
    assert result["provider"] == "jira"
    assert result["status"] == "OPEN"
    assert result["externalUrl"].startswith("https://jira.example.com/browse/")
    assert result["duplicate"] is False
    assert metadata_store.records[0]["actionItemId"] == "act_123"
    assert metadata_store.records[0]["providerProjectKey"] == "PROJ"


def test_integration_service_skips_duplicate_creation():
    metadata_store = InMemoryMetadataStore()
    service = IntegrationService(metadata_store=metadata_store)

    first = service.create_external_task(_event())
    assert first["eventType"] == "external.task.created"
    assert first["duplicate"] is False

    # Same action_item_id + provider + project_key → should not call connector again.
    second = service.create_external_task(_event())
    assert second["eventType"] == "external.task.exists"
    assert second["duplicate"] is True
    assert second["externalId"] == first["externalId"]
    assert len(metadata_store.records) == 1  # Only one record written.


def test_integration_service_allows_same_item_for_different_providers():
    metadata_store = InMemoryMetadataStore()
    service = IntegrationService(metadata_store=metadata_store)

    jira = service.create_external_task(_event(provider="jira", project_key="PROJ"))
    github = service.create_external_task(_event(provider="github", project_key="myorg/myrepo"))

    assert jira["eventType"] == "external.task.created"
    assert github["eventType"] == "external.task.created"
    assert len(metadata_store.records) == 2


def test_integration_service_allows_same_item_for_different_project_keys():
    metadata_store = InMemoryMetadataStore()
    service = IntegrationService(metadata_store=metadata_store)

    r1 = service.create_external_task(_event(project_key="PROJECT-A"))
    r2 = service.create_external_task(_event(project_key="PROJECT-B"))

    assert r1["eventType"] == "external.task.created"
    assert r2["eventType"] == "external.task.created"
    assert len(metadata_store.records) == 2
