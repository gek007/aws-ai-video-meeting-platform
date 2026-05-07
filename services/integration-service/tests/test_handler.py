from integration_service.handler import lambda_handler


def test_integration_handler_returns_external_task():
    response = lambda_handler(
        {"provider": "jira", "items": [{"actionItemId": "act_123", "title": "Fix login", "description": "Investigate timeout"}]},
        None,
    )
    assert response["statusCode"] == 201
    assert response["body"]["result"]["eventType"] == "external.task.created"
