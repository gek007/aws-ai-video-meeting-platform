from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True, slots=True)
class DeliveryResult:
    provider: str
    delivery_id: str


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
        if self._client_factory is not None:
            return self._client_factory()

        import boto3

        return boto3.client("ses")
