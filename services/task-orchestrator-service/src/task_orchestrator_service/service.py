from __future__ import annotations


class TaskOrchestratorService:
    def orchestrate(self, event: dict) -> dict:
        items = event.get("actionItems", [])
        return {
            "eventType": "task.creation.requested",
            "tenantId": event["tenantId"],
            "meetingId": event["meetingId"],
            "videoItemId": event["videoItemId"],
            "items": items,
            "provider": "jira",
        }

