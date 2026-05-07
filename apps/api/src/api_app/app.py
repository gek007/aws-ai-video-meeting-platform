from __future__ import annotations

import os

from api_app.uploader import InMemoryUploader, S3PresignedUploader
from chat_rag_service.answerer import BedrockAnswerer, InMemoryAnswerer
from chat_rag_service.retriever import InMemoryRetriever, OpenSearchRetriever
from chat_rag_service.service import ChatRAGService
from search_query_service.service import SearchQueryService
from shared.repository import InMemoryRepository

_repository = InMemoryRepository()


def healthcheck() -> dict:
    return {"status": "ok", "service": "api"}


def init_upload(filename: str, tenant_id: str, content_type: str = "video/mp4") -> dict:
    uploader = S3PresignedUploader() if os.getenv("RAW_VIDEO_BUCKET") else InMemoryUploader()
    session = uploader.create_upload_session(
        filename=filename,
        tenant_id=tenant_id,
        content_type=content_type,
    )
    return {
        "meetingId": session.meeting_id,
        "videoItemId": session.video_item_id,
        "uploadUrl": session.upload_url,
        "s3Bucket": session.s3_bucket,
        "s3Key": session.s3_key,
        "expiresIn": session.expires_in,
        "method": session.method,
        "fields": session.fields,
    }


def get_meeting(meeting_id: str) -> dict | None:
    return _repository.get_meeting(meeting_id)


def get_meeting_summary(meeting_id: str) -> dict | None:
    return _repository.get_summary(meeting_id)


def get_related_meetings(meeting_id: str, tenant_id: str = "tenant_demo") -> dict:
    return SearchQueryService().related_meetings(tenant_id=tenant_id, meeting_id=meeting_id)


def get_meeting_action_items(meeting_id: str) -> list[dict]:
    return _repository.get_action_items(meeting_id)


def get_video_item(video_item_id: str) -> dict | None:
    return _repository.get_video_item(video_item_id)


def search_meetings(query: str) -> dict:
    return _repository.search_meetings(query)


def ask_meeting_question(meeting_id: str, question: str, tenant_id: str = "tenant_demo") -> dict:
    retriever = _build_retriever(meeting_id=meeting_id, tenant_id=tenant_id)
    answerer = BedrockAnswerer() if os.getenv("BEDROCK_MODEL_ID") else InMemoryAnswerer()
    return ChatRAGService(retriever=retriever, answerer=answerer).answer(
        question=question,
        meeting_id=meeting_id,
        tenant_id=tenant_id,
    )


def get_chat_sessions(meeting_id: str) -> list[dict]:
    return _repository.get_chat_sessions(meeting_id)


def get_chat_messages(session_id: str) -> list[dict]:
    return _repository.get_chat_messages(session_id)


def connect_integration(provider: str) -> dict:
    return {"provider": provider, "status": "connected"}


def sync_task(task_id: str) -> dict:
    return {"taskId": task_id, "status": "sync_requested"}


def _build_retriever(meeting_id: str, tenant_id: str):
    if os.getenv("OPENSEARCH_ENDPOINT"):
        return OpenSearchRetriever()
    # Fall back to repository-backed chunks for local / no-vector-store environments.
    chunks = _repository.get_transcript_chunks(meeting_id=meeting_id, tenant_id=tenant_id)
    return InMemoryRetriever(chunks=chunks)
