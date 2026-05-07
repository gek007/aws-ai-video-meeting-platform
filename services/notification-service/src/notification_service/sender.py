from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True, slots=True)
class DeliveryResult:
    provider: str
    delivery_id: str
    status: str = "sent"


@dataclass(slots=True)
class InMemoryNotificationSender:
    deliveries: list[dict] = field(default_factory=list)

    def send(
        self,
        *,
        channel: str,
        recipient: str,
        subject: str,
        message: str,
    ) -> DeliveryResult:
        delivery_id = f"in-memory-{len(self.deliveries) + 1}"
        self.deliveries.append(
            {
                "channel": channel,
                "recipient": recipient,
                "subject": subject,
                "message": message,
                "deliveryId": delivery_id,
            }
        )
        return DeliveryResult(provider="in-memory", delivery_id=delivery_id)


class SESNotificationSender:
    def __init__(
        self,
        source_email: str | None = None,
        client_factory: Callable[[], object] | None = None,
    ) -> None:
        self._source_email = source_email or os.getenv("SES_SOURCE_EMAIL")
        if not self._source_email:
            raise ValueError("SES_SOURCE_EMAIL is required for SESNotificationSender.")
        self._client_factory = client_factory
        self._cached_client: object | None = None

    def send(
        self,
        *,
        channel: str,
        recipient: str,
        subject: str,
        message: str,
    ) -> DeliveryResult:
        if channel != "email":
            raise ValueError("SESNotificationSender supports only email notifications.")

        response = self._client.send_email(
            Source=self._source_email,
            Destination={"ToAddresses": [recipient]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": message}},
            },
        )
        return DeliveryResult(provider="ses", delivery_id=response["MessageId"])

    @property
    def _client(self):
        if self._cached_client is None:
            if self._client_factory is not None:
                self._cached_client = self._client_factory()
            else:
                import boto3
                self._cached_client = boto3.client("ses")
        return self._cached_client


class SlackWebhookSender:
    """Delivers notifications to a Slack channel via an incoming webhook URL."""

    def __init__(
        self,
        webhook_url: str | None = None,
        http_client_factory: Callable[[], object] | None = None,
    ) -> None:
        self._webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        if not self._webhook_url and http_client_factory is None:
            raise ValueError("SLACK_WEBHOOK_URL is required for SlackWebhookSender.")
        self._http_client_factory = http_client_factory

    def send(
        self,
        *,
        channel: str,
        recipient: str,
        subject: str,
        message: str,
    ) -> DeliveryResult:
        if channel != "slack":
            raise ValueError("SlackWebhookSender supports only slack notifications.")

        payload = {
            "text": f"*{subject}*\n{message}",
            "username": "Meeting Intelligence",
        }
        response = self._post(payload)
        delivery_id = response.get("ts") or f"slack-{hash(message) & 0xFFFFFF:x}"
        return DeliveryResult(provider="slack", delivery_id=delivery_id)

    def _post(self, payload: dict) -> dict:
        import json

        if self._http_client_factory is not None:
            client = self._http_client_factory()
            return client.post(self._webhook_url, json=payload)

        import urllib.request

        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            self._webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode()
            try:
                import json as _json
                return _json.loads(body)
            except Exception:
                return {}


class CompositeSender:
    """Routes notifications to the appropriate backend based on channel."""

    def __init__(self, senders: dict) -> None:
        self._senders = senders

    def send(
        self,
        *,
        channel: str,
        recipient: str,
        subject: str,
        message: str,
    ) -> DeliveryResult:
        sender = self._senders.get(channel)
        if sender is None:
            raise ValueError(f"No sender configured for channel: {channel!r}")
        return sender.send(channel=channel, recipient=recipient, subject=subject, message=message)
