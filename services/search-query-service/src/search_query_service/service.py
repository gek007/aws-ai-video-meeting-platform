from __future__ import annotations


class SearchQueryService:
    def related_meetings(self, meeting_id: str) -> dict:
        return {
            "meetingId": meeting_id,
            "results": [
                {"meetingId": "mtg_related_001", "score": 0.92, "reason": "Similar authentication discussion"},
            ],
        }

