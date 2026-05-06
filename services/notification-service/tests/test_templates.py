from notification_service.service import NotificationService


def test_notification_service_uses_template_message():
    result = NotificationService().notify({"templateName": "task_status_changed"})

    assert result["templateName"] == "task_status_changed"
    assert result["message"] == "An external task status was updated."

