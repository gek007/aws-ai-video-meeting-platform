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
