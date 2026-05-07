from integration_service.service import IntegrationService
from integration_service.store import InMemoryMetadataStore


def test_integration_service_returns_external_task_metadata():
    metadata_store = InMemoryMetadataStore()
    result = IntegrationService(metadata_store=metadata_store).create_external_task(
        {
            "provider": "jira",
            "tenantId": "tenant_demo",
            "items": [{"actionItemId": "act_123", "title": "Fix login timeout", "description": "Investigate issue"}],
        }
    )

    assert result["eventType"] == "external.task.created"
    assert result["actionItemId"] == "act_123"
    assert result["provider"] == "jira"
    assert result["status"] == "OPEN"
    assert result["externalUrl"].startswith("https://jira.example.com/browse/")
    assert metadata_store.records[0]["actionItemId"] == "act_123"
