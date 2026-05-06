from status_observer_service.service import StatusObserverService


def test_status_observer_service_returns_default_done_status():
    result = StatusObserverService().sync({})

    assert result["eventType"] == "task.status.changed"
    assert result["provider"] == "jira"
    assert result["status"] == "DONE"

