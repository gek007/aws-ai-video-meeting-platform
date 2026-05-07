from status_observer_service.handler import lambda_handler


def test_status_observer_returns_status_change():
    response = lambda_handler({}, None)
    assert response["body"]["result"]["eventType"] == "task.status.changed"
    assert response["body"]["result"]["tenantId"] == "tenant_demo"
    assert response["body"]["result"]["status"] == "DONE"
