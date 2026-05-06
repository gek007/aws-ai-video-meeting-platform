from __future__ import annotations

from shared.repository import InMemoryRepository


class ChatRAGService:
    def __init__(self, repository: InMemoryRepository | None = None) -> None:
        self._repository = repository or InMemoryRepository()

    def answer(self, question: str, meeting_id: str, tenant_id: str = "tenant_demo") -> dict:
        meeting = self._repository.get_meeting(meeting_id)
        if not meeting or meeting["tenantId"] != tenant_id:
            return {
                "meetingId": meeting_id,
                "answer": "Not enough information is available for this meeting.",
                "citations": [],
                "confidence": "low",
            }

        summary = self._repository.get_summary(meeting_id)
        action_items = self._repository.get_action_items(meeting_id)
        if not summary:
            return {
                "meetingId": meeting_id,
                "answer": "Not enough information is available for this meeting.",
                "citations": [],
                "confidence": "low",
            }

        return {
            "meetingId": meeting_id,
            "answer": f"{summary['summary']} Question answered: {question}",
            "citations": [
                {
                    "type": "transcript_chunk",
                    "chunkId": "chunk_001",
                    "startOffsetSeconds": 120,
                    "endOffsetSeconds": 155,
                }
            ]
            + (
                [
                    {
                        "type": "action_item",
                        "actionItemId": action_items[0]["id"],
                    }
                ]
                if action_items
                else []
            ),
            "confidence": "medium" if action_items else "low",
        }
