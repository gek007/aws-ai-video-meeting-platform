from chat_rag_service.service import ChatRAGService
from shared.repository import InMemoryRepository


def test_chat_rag_rejects_wrong_tenant():
    service = ChatRAGService(InMemoryRepository())
    result = service.answer("What was decided?", "mtg_123", tenant_id="tenant_other")

    assert result["confidence"] == "low"
    assert result["citations"] == []

