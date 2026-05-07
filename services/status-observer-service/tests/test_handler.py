import json

from status_observer_service.handler import lambda_handler


def test_status_observer_syncs_new_task_with_no_prior_record():
    response = lambda_handler(
        {"tenantId": "tenant_demo", "provider": "jira", "externalId": "jira-001", "status": "DONE"},
        None,
    )
    assert response["statusCode"] == 200
    result = json.loads(response["body"])["result"]
    assert result["eventType"] == "task.status.synced"
    assert result["tenantId"] == "tenant_demo"
    assert result["status"] == "DONE"
    assert result["statusChanged"] is False
