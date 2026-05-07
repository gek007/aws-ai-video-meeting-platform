from chat_rag_service.answerer import INSUFFICIENT_INFORMATION
from chat_rag_service.retriever import InMemoryRetriever
from chat_rag_service.service import ChatRAGService


def _chunk_fixture(meeting_id="mtg_123", tenant_id="tenant_123"):
    return {
        "chunkId": "chunk_001",
        "meetingId": meeting_id,
        "tenantId": tenant_id,
        "videoItemId": "vid_123",
        "chunkText": "Login timeout fix was agreed upon.",
        "score": 0.95,
        "startOffsetSeconds": 120.0,
        "endOffsetSeconds": 155.0,
    }


def test_chat_rag_service_returns_answer_with_citations():
    retriever = InMemoryRetriever(chunks=[_chunk_fixture()])
    service = ChatRAGService(retriever=retriever)
    result = service.answer("What was decided?", "mtg_123", "tenant_123")

    assert result["meetingId"] == "mtg_123"
    assert result["answer"] != INSUFFICIENT_INFORMATION
    assert len(result["citations"]) > 0
    assert result["citations"][0]["chunkId"] == "chunk_001"
    assert result["confidence"] in ("high", "medium", "low")


def test_chat_rag_service_returns_insufficient_when_no_chunks():
    retriever = InMemoryRetriever(chunks=[])
    service = ChatRAGService(retriever=retriever)
    result = service.answer("What was decided?", "mtg_missing", "tenant_123")

    assert result["answer"] == INSUFFICIENT_INFORMATION
    assert result["citations"] == []
    assert result["confidence"] == "low"


def test_chat_rag_service_filters_by_tenant():
    chunks = [
        _chunk_fixture(meeting_id="mtg_123", tenant_id="tenant_A"),
        _chunk_fixture(meeting_id="mtg_123", tenant_id="tenant_B"),
    ]
    retriever = InMemoryRetriever(chunks=chunks)
    service = ChatRAGService(retriever=retriever)
    result = service.answer("Q", "mtg_123", "tenant_A")

    # Should only find chunks from tenant_A
    assert all(c["meetingId"] == "mtg_123" for c in result["citations"])


def test_chat_rag_service_response_includes_question_and_meeting():
    retriever = InMemoryRetriever(chunks=[_chunk_fixture()])
    result = ChatRAGService(retriever=retriever).answer("What was decided?", "mtg_123", "tenant_123")

    assert result["question"] == "What was decided?"
    assert result["meetingId"] == "mtg_123"
    assert "usedRelatedMeetings" in result
