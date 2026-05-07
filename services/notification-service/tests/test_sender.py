import pytest
from notification_service.sender import CompositeSender, InMemoryNotificationSender, SESNotificationSender, SlackWebhookSender


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


def test_slack_webhook_sender_raises_without_url():
    with pytest.raises(ValueError, match="SLACK_WEBHOOK_URL"):
        SlackWebhookSender()


def test_slack_webhook_sender_posts_message():
    calls = []

    def fake_http_factory():
        class _Client:
            def post(self, url, json=None):
                calls.append({"url": url, "json": json})
                return {"ts": "slack-ts-001"}
        return _Client()

    sender = SlackWebhookSender(webhook_url="https://hooks.slack.com/T/B/x", http_client_factory=fake_http_factory)
    result = sender.send(
        channel="slack",
        recipient="#general",
        subject="Meeting summary ready",
        message="Summary is now available.",
    )

    assert result.provider == "slack"
    assert result.delivery_id == "slack-ts-001"
    assert len(calls) == 1
    assert "Meeting summary ready" in calls[0]["json"]["text"]


def test_slack_webhook_sender_rejects_non_slack_channel():
    sender = SlackWebhookSender(webhook_url="https://hooks.slack.com/T/B/x")
    with pytest.raises(ValueError, match="slack"):
        sender.send(channel="email", recipient="u@e.com", subject="s", message="m")


def test_composite_sender_routes_by_channel():
    email_sender = InMemoryNotificationSender()
    slack_sender = InMemoryNotificationSender()
    composite = CompositeSender(senders={"email": email_sender, "slack": slack_sender})

    composite.send(channel="email", recipient="u@e.com", subject="s", message="m")
    composite.send(channel="slack", recipient="#ch", subject="s", message="m")

    assert len(email_sender.deliveries) == 1
    assert len(slack_sender.deliveries) == 1


def test_composite_sender_raises_for_unknown_channel():
    composite = CompositeSender(senders={"email": InMemoryNotificationSender()})
    with pytest.raises(ValueError, match="teams"):
        composite.send(channel="teams", recipient="u", subject="s", message="m")
