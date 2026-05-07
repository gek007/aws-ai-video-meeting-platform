from __future__ import annotations

from typing import Protocol

from notification_service.sender import DeliveryResult
from shared.ids import new_id


class MetadataStore(Protocol):
    def record_notification(
        self,
        *,
        tenant_id: str,
        meeting_id: str | None,
        video_item_id: str | None,
        recipient: str,
        channel: str,
        template_name: str,
        status: str,
    ) -> None: ...


class NotificationSender(Protocol):
    def send(
        self,
        *,
        channel: str,
        recipient: str,
        subject: str,
        message: str,
    ) -> DeliveryResult: ...


class NotificationService:
    TEMPLATES = {
        "summary_ready": "Meeting summary is ready.",
        "action_item_created": "A new action item was created from the meeting.",
        "task_status_changed": "An external task status was updated.",
    }
    SUBJECTS = {
        "summary_ready": "Meeting summary ready",
        "action_item_created": "New action item created",
        "task_status_changed": "Task status updated",
    }

    def __init__(self, metadata_store: MetadataStore, sender: NotificationSender) -> None:
        self._metadata_store = metadata_store
        self._sender = sender

    def notify(self, event: dict) -> dict:
        template_name = event.get("templateName", "summary_ready")
        message = event.get("message", self.TEMPLATES.get(template_name, self.TEMPLATES["summary_ready"]))
        subject = event.get("subject", self.SUBJECTS.get(template_name, self.SUBJECTS["summary_ready"]))
        channel = event.get("channel", "email")
        recipient = event.get("recipient", "participant@example.com")
        delivery = self._sender.send(
            channel=channel,
            recipient=recipient,
            subject=subject,
            message=message,
        )
        result = {
            "eventType": "notification.sent",
            "notificationId": new_id("ntf"),
            "channel": channel,
            "recipient": recipient,
            "templateName": template_name,
            "status": "sent",
            "message": message,
            "subject": subject,
            "provider": delivery.provider,
            "deliveryId": delivery.delivery_id,
        }
        self._metadata_store.record_notification(
            tenant_id=event.get("tenantId", "tenant_demo"),
            meeting_id=event.get("meetingId"),
            video_item_id=event.get("videoItemId"),
            recipient=result["recipient"],
            channel=result["channel"],
            template_name=result["templateName"],
            status=result["status"],
        )
        return result
