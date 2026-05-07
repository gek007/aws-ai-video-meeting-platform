import json

from status_observer_service.handler import lambda_handler


def test_status_observer_returns_status_change():
    response = lambda_handler({}, None)
    body = json.loads(response["body"])
    assert body["result"]["eventType"] == "task.status.changed"
    assert body["result"]["tenantId"] == "tenant_demo"
    assert body["result"]["status"] == "DONE"
