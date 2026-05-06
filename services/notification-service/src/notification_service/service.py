from __future__ import annotations


class NotificationService:
    TEMPLATES = {
        "summary_ready": "Meeting summary is ready.",
        "action_item_created": "A new action item was created from the meeting.",
        "task_status_changed": "An external task status was updated.",
    }

    def notify(self, event: dict) -> dict:
        template_name = event.get("templateName", "summary_ready")
        return {
            "eventType": "notification.sent",
            "channel": event.get("channel", "email"),
            "recipient": event.get("recipient", "participant@example.com"),
            "templateName": template_name,
            "message": event.get("message", self.TEMPLATES.get(template_name, self.TEMPLATES["summary_ready"])),
        }
