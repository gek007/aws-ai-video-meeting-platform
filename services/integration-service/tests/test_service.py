from integration_service.service import IntegrationService


def test_integration_service_returns_external_task_metadata():
    result = IntegrationService().create_external_task(
        {
            "provider": "jira",
            "items": [{"title": "Fix login timeout", "description": "Investigate issue"}],
        }
    )

    assert result["eventType"] == "external.task.created"
    assert result["provider"] == "jira"
    assert result["status"] == "OPEN"
    assert result["externalUrl"].startswith("https://jira.example.com/browse/")
