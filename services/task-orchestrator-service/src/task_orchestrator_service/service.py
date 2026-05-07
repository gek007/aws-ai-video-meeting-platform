from __future__ import annotations

from shared.ids import new_id


class TaskOrchestratorService:
    def orchestrate(self, event: dict) -> dict:
        items = []
        for item in event.get("actionItems", []):
            enriched_item = dict(item)
            enriched_item.setdefault("actionItemId", new_id("act"))
            items.append(enriched_item)
        return {
            "eventType": "task.creation.requested",
            "tenantId": event["tenantId"],
            "meetingId": event["meetingId"],
            "videoItemId": event["videoItemId"],
            "items": items,
            "provider": event.get("provider") or event.get("taskProvider", "jira"),
        }
