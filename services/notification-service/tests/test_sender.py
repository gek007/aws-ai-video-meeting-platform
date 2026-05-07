from notification_service.sender import InMemoryNotificationSender, SESNotificationSender


class StubSESClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def send_email(self, **kwargs):
        self.calls.append(kwargs)
        return {"MessageId": "ses-msg-123"}


def test_inmemory_notification_sender_records_delivery():
    sender = InMemoryNotificationSender()

    result = sender.send(
        channel="email",
        recipient="user@example.com",
        subject="Meeting summary ready",
        message="Meeting summary is ready.",
    )

    assert result.provider == "in-memory"
    assert sender.deliveries[0]["recipient"] == "user@example.com"


def test_ses_notification_sender_sends_email():
    client = StubSESClient()
    sender = SESNotificationSender(
        source_email="noreply@example.com",
        client_factory=lambda: client,
    )

    result = sender.send(
        channel="email",
        recipient="user@example.com",
        subject="Meeting summary ready",
        message="Meeting summary is ready.",
    )

    assert result.provider == "ses"
    assert result.delivery_id == "ses-msg-123"
    assert client.calls[0]["Source"] == "noreply@example.com"
    assert client.calls[0]["Destination"]["ToAddresses"] == ["user@example.com"]
