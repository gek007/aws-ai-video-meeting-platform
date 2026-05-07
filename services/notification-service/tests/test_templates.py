from notification_service.service import NotificationService
from notification_service.sender import InMemoryNotificationSender
from notification_service.store import InMemoryMetadataStore


def test_notification_service_uses_template_message():
    result = NotificationService(
        metadata_store=InMemoryMetadataStore(),
        sender=InMemoryNotificationSender(),
    ).notify({"templateName": "task_status_changed"})

    assert result["templateName"] == "task_status_changed"
    assert result["message"] == "An external task status was updated."
    assert result["subject"] == "Task status updated"
