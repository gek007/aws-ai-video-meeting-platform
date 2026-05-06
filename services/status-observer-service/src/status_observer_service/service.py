from __future__ import annotations


class StatusObserverService:
    def sync(self, event: dict) -> dict:
        return {
            "eventType": "task.status.changed",
            "provider": event.get("provider", "jira"),
            "externalId": event.get("externalId", "jira-001"),
            "status": event.get("status", "DONE"),
        }

