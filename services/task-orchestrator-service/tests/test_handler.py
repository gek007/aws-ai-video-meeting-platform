from task_orchestrator_service.handler import lambda_handler


def test_task_orchestrator_returns_creation_request():
    response = lambda_handler(
        {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
            "actionItems": [{"title": "Fix bug"}],
        },
        None,
    )
    assert response["body"]["nextEvent"]["eventType"] == "task.creation.requested"

