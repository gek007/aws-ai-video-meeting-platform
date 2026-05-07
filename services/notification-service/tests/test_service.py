from notification_service.service import NotificationService
from notification_service.sender import InMemoryNotificationSender
from notification_service.store import InMemoryMetadataStore


def test_notification_service_uses_defaults_when_optional_fields_missing():
    metadata_store = InMemoryMetadataStore()
    sender = InMemoryNotificationSender()
    result = NotificationService(metadata_store=metadata_store, sender=sender).notify({})

    assert result["eventType"] == "notification.sent"
    assert result["channel"] == "email"
    assert result["recipient"] == "participant@example.com"
    assert result["status"] == "sent"
    assert result["provider"] == "in-memory"
    assert result["subject"] == "Meeting summary ready"
    assert metadata_store.records[0]["status"] == "sent"
