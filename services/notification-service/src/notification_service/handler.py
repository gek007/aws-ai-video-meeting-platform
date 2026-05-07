from __future__ import annotations

import os

from notification_service.sender import (
    CompositeSender,
    InMemoryNotificationSender,
    SESNotificationSender,
    SlackWebhookSender,
)
from notification_service.service import NotificationService
from notification_service.store import AuroraNotificationStore, InMemoryMetadataStore
from shared.responses import json_response


def lambda_handler(event: dict, _context) -> dict:
    metadata_store = _build_metadata_store()
    sender = _build_sender()
    result = NotificationService(metadata_store=metadata_store, sender=sender).notify(event)
    return json_response(200, {"message": "Notification processed.", "result": result})


def _build_metadata_store():
    if os.getenv("AURORA_DATABASE_URL") or os.getenv("DATABASE_URL"):
        return AuroraNotificationStore()
    return InMemoryMetadataStore()


def _build_sender():
    senders = {}

    if os.getenv("SES_SOURCE_EMAIL"):
        senders["email"] = SESNotificationSender()
    else:
        senders["email"] = InMemoryNotificationSender()

    if os.getenv("SLACK_WEBHOOK_URL"):
        senders["slack"] = SlackWebhookSender()
    else:
        senders["slack"] = InMemoryNotificationSender()

    return CompositeSender(senders=senders)
