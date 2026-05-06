from chat_rag_service.service import ChatRAGService


def test_chat_rag_service_returns_answer_and_citations():
    result = ChatRAGService().answer("What was decided?", "mtg_123")

    assert result["meetingId"] == "mtg_123"
    assert "What was decided?" in result["answer"]
    assert result["citations"][0]["chunkId"] == "chunk_001"
    assert result["confidence"] == "medium"

