from chat_rag_service.retriever import InMemoryRetriever
from chat_rag_service.service import ChatRAGService


def test_chat_rag_rejects_wrong_tenant():
    chunks = [
        {
            "chunkId": "chunk_001",
            "meetingId": "mtg_123",
            "tenantId": "tenant_correct",
            "videoItemId": "vid_123",
            "chunkText": "We decided to fix the login timeout.",
            "score": 0.95,
        }
    ]
    retriever = InMemoryRetriever(chunks=chunks)
    service = ChatRAGService(retriever=retriever)

    # Request from a different tenant should get no chunks → insufficient info
    result = service.answer("What was decided?", "mtg_123", tenant_id="tenant_other")

    assert result["confidence"] == "low"
    assert result["citations"] == []


def test_chat_rag_allows_correct_tenant():
    chunks = [
        {
            "chunkId": "chunk_001",
            "meetingId": "mtg_123",
            "tenantId": "tenant_correct",
            "videoItemId": "vid_123",
            "chunkText": "Login timeout decision content.",
            "score": 0.95,
        }
    ]
    retriever = InMemoryRetriever(chunks=chunks)
    service = ChatRAGService(retriever=retriever)
    result = service.answer("What was decided?", "mtg_123", tenant_id="tenant_correct")

    assert len(result["citations"]) > 0
    assert result["confidence"] != "low" or len(result["citations"]) > 0
