from integration_service.service import IntegrationService


def test_integration_service_supports_github_provider():
    result = IntegrationService().create_external_task(
        {
            "provider": "github",
            "items": [{"title": "Fix login timeout", "description": "Investigate issue"}],
        }
    )

    assert result["provider"] == "github"
    assert result["externalId"] == "GH-101"

