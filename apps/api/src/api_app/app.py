from __future__ import annotations

from chat_rag_service.service import ChatRAGService
from search_query_service.service import SearchQueryService
from shared.repository import InMemoryRepository

_repository = InMemoryRepository()


def healthcheck() -> dict:
    return {"status": "ok", "service": "api"}


def init_upload(filename: str, tenant_id: str) -> dict:
    return {
        "uploadUrl": f"https://uploads.example.com/{tenant_id}/{filename}",
        "method": "PUT",
        "headers": {"x-tenant-id": tenant_id},
    }


def get_meeting(meeting_id: str) -> dict | None:
    return _repository.get_meeting(meeting_id)


def get_meeting_summary(meeting_id: str) -> dict | None:
    return _repository.get_summary(meeting_id)


def get_related_meetings(meeting_id: str) -> dict:
    return SearchQueryService().related_meetings(meeting_id)


def get_meeting_action_items(meeting_id: str) -> list[dict]:
    return _repository.get_action_items(meeting_id)


def get_video_item(video_item_id: str) -> dict | None:
    return _repository.get_video_item(video_item_id)


def search_meetings(query: str) -> dict:
    return _repository.search_meetings(query)


def ask_meeting_question(meeting_id: str, question: str, tenant_id: str = "tenant_demo") -> dict:
    return ChatRAGService(_repository).answer(question=question, meeting_id=meeting_id, tenant_id=tenant_id)


def get_chat_sessions(meeting_id: str) -> list[dict]:
    return _repository.get_chat_sessions(meeting_id)


def get_chat_messages(session_id: str) -> list[dict]:
    return _repository.get_chat_messages(session_id)


def connect_integration(provider: str) -> dict:
    return {"provider": provider, "status": "connected"}


def sync_task(task_id: str) -> dict:
    return {"taskId": task_id, "status": "sync_requested"}
