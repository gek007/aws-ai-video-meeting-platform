from __future__ import annotations

from typing import Protocol

from chat_rag_service.answerer import AnswerResult, InMemoryAnswerer
from chat_rag_service.retriever import InMemoryRetriever, RetrievedChunk


class Retriever(Protocol):
    def retrieve(
        self,
        *,
        question: str,
        meeting_id: str,
        tenant_id: str,
        top_k: int,
    ) -> list[RetrievedChunk]: ...


class Answerer(Protocol):
    def answer(self, *, question: str, chunks: list[RetrievedChunk], context: dict) -> AnswerResult: ...


class ChatRAGService:
    def __init__(
        self,
        retriever: Retriever | None = None,
        answerer: Answerer | None = None,
    ) -> None:
        self._retriever = retriever or InMemoryRetriever()
        self._answerer = answerer or InMemoryAnswerer()

    def answer(self, question: str, meeting_id: str, tenant_id: str = "tenant_demo") -> dict:
        chunks = self._retriever.retrieve(
            question=question,
            meeting_id=meeting_id,
            tenant_id=tenant_id,
            top_k=5,
        )
        context = {"meetingId": meeting_id, "tenantId": tenant_id}
        result = self._answerer.answer(question=question, chunks=chunks, context=context)
        return {
            "meetingId": meeting_id,
            "question": question,
            "answer": result.answer,
            "citations": result.citations,
            "confidence": result.confidence,
            "usedRelatedMeetings": False,
        }
