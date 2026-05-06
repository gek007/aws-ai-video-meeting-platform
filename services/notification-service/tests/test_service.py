from notification_service.service import NotificationService


def test_notification_service_uses_defaults_when_optional_fields_missing():
    result = NotificationService().notify({})

    assert result["eventType"] == "notification.sent"
    assert result["channel"] == "email"
    assert result["recipient"] == "participant@example.com"

