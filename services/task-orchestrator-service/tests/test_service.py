from task_orchestrator_service.service import TaskOrchestratorService


def test_task_orchestrator_preserves_action_items_and_provider():
    result = TaskOrchestratorService().orchestrate(
        {
            "tenantId": "tenant_123",
            "meetingId": "mtg_123",
            "videoItemId": "vid_123",
            "actionItems": [{"title": "Fix login timeout"}],
        }
    )

    assert result["eventType"] == "task.creation.requested"
    assert result["provider"] == "jira"
    assert result["items"][0]["title"] == "Fix login timeout"

