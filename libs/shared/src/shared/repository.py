from __future__ import annotations


class InMemoryRepository:
    def __init__(self) -> None:
        self.meetings = {
            "mtg_123": {
                "id": "mtg_123",
                "tenantId": "tenant_demo",
                "title": "Authentication Reliability Review",
                "status": "processed",
            }
        }
        self.video_items = {
            "vid_123": {
                "id": "vid_123",
                "meetingId": "mtg_123",
                "tenantId": "tenant_demo",
                "processingStatus": "completed",
                "transcriptionStatus": "completed",
                "aiEnrichmentStatus": "completed",
            }
        }
        self.summaries = {
            "mtg_123": {
                "meetingId": "mtg_123",
                "summary": "Authentication issues and action items were reviewed.",
                "topics": ["authentication", "timeouts"],
            }
        }
        self.action_items = {
            "mtg_123": [
                {
                    "id": "ai_123",
                    "title": "Fix login timeout issue",
                    "itemType": "bug",
                    "status": "open",
                }
            ]
        }
        self.chat_sessions = {
            "mtg_123": [
                {
                    "id": "chat_session_001",
                    "meetingId": "mtg_123",
                    "title": "Default session",
                }
            ]
        }
        self.chat_messages = {
            "chat_session_001": [
                {
                    "id": "msg_001",
                    "role": "user",
                    "message": "What was decided?",
                }
            ]
        }
        self.transcript_chunks = [
            {
                "chunkId": "chunk_001",
                "meetingId": "mtg_123",
                "tenantId": "tenant_demo",
                "videoItemId": "vid_123",
                "chunkText": "We decided to prioritise fixing the login timeout issue. The team agreed it blocks users.",
                "score": 0.95,
                "startOffsetSeconds": 120.0,
                "endOffsetSeconds": 155.0,
            },
            {
                "chunkId": "chunk_002",
                "meetingId": "mtg_123",
                "tenantId": "tenant_demo",
                "videoItemId": "vid_123",
                "chunkText": "Authentication reliability was discussed. Several timeout scenarios were identified.",
                "score": 0.88,
                "startOffsetSeconds": 60.0,
                "endOffsetSeconds": 95.0,
            },
        ]
        self.search_results = [
            {
                "meetingId": "mtg_123",
                "title": "Authentication Reliability Review",
                "score": 0.98,
            }
        ]

    def get_meeting(self, meeting_id: str) -> dict | None:
        return self.meetings.get(meeting_id)

    def get_summary(self, meeting_id: str) -> dict | None:
        return self.summaries.get(meeting_id)

    def get_action_items(self, meeting_id: str) -> list[dict]:
        return self.action_items.get(meeting_id, [])

    def get_video_item(self, video_item_id: str) -> dict | None:
        return self.video_items.get(video_item_id)

    def search_meetings(self, query: str) -> dict:
        return {
            "query": query,
            "results": self.search_results,
        }

    def get_chat_sessions(self, meeting_id: str) -> list[dict]:
        return self.chat_sessions.get(meeting_id, [])

    def get_chat_messages(self, session_id: str) -> list[dict]:
        return self.chat_messages.get(session_id, [])

    def get_transcript_chunks(self, meeting_id: str, tenant_id: str) -> list[dict]:
        return [
            c for c in self.transcript_chunks
            if c["meetingId"] == meeting_id and c["tenantId"] == tenant_id
        ]

