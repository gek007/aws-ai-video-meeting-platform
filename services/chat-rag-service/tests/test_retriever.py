import pytest
from chat_rag_service.retriever import InMemoryRetriever, OpenSearchRetriever


def _chunks(meeting_id="mtg_123", tenant_id="tenant_123"):
    return [
        {
            "chunkId": "chunk_001",
            "meetingId": meeting_id,
            "tenantId": tenant_id,
            "videoItemId": "vid_123",
            "chunkText": "We decided to fix the login timeout issue.",
            "score": 0.95,
            "startOffsetSeconds": 120.0,
            "endOffsetSeconds": 155.0,
        },
        {
            "chunkId": "chunk_002",
            "meetingId": meeting_id,
            "tenantId": tenant_id,
            "videoItemId": "vid_123",
            "chunkText": "Authentication was the main topic discussed.",
            "score": 0.88,
        },
    ]


def test_in_memory_retriever_returns_chunks_for_meeting():
    retriever = InMemoryRetriever(chunks=_chunks())
    results = retriever.retrieve(question="What was decided?", meeting_id="mtg_123", tenant_id="tenant_123", top_k=5)

    assert len(results) == 2
    assert results[0].chunk_id == "chunk_001"
    assert results[0].meeting_id == "mtg_123"


def test_in_memory_retriever_filters_by_tenant():
    chunks = _chunks() + _chunks(meeting_id="mtg_123", tenant_id="other_tenant")
    retriever = InMemoryRetriever(chunks=chunks)
    results = retriever.retrieve(question="Q", meeting_id="mtg_123", tenant_id="tenant_123", top_k=10)

    assert all(c.meeting_id == "mtg_123" for c in results)
    # Only the 2 from tenant_123 should be returned
    assert len(results) == 2


def test_in_memory_retriever_respects_top_k():
    retriever = InMemoryRetriever(chunks=_chunks())
    results = retriever.retrieve(question="Q", meeting_id="mtg_123", tenant_id="tenant_123", top_k=1)
    assert len(results) == 1


def test_in_memory_retriever_returns_empty_for_unknown_meeting():
    retriever = InMemoryRetriever(chunks=_chunks())
    results = retriever.retrieve(question="Q", meeting_id="mtg_unknown", tenant_id="tenant_123", top_k=5)
    assert results == []


def test_opensearch_retriever_raises_without_endpoint():
    with pytest.raises(ValueError, match="OPENSEARCH_ENDPOINT"):
        OpenSearchRetriever()


def test_opensearch_retriever_embeds_question_and_searches():
    import io, json

    embed_calls = []
    search_calls = []

    def fake_embed_client():
        class _Client:
            def invoke_model(self, **kwargs):
                embed_calls.append(kwargs)
                return {"body": io.BytesIO(json.dumps({"embedding": [0.1] * 10}).encode())}
        return _Client()

    def fake_search_client():
        class _Client:
            def search(self, index, body):
                search_calls.append({"index": index, "body": body})
                return {
                    "hits": {
                        "hits": [
                            {
                                "_id": "chunk_001",
                                "_score": 0.95,
                                "_source": {
                                    "meetingId": "mtg_123",
                                    "videoItemId": "vid_123",
                                    "tenantId": "tenant_123",
                                    "chunkText": "Login timeout fix discussion.",
                                    "startOffsetSeconds": 120.0,
                                    "endOffsetSeconds": 155.0,
                                },
                            }
                        ]
                    }
                }
        return _Client()

    retriever = OpenSearchRetriever(
        endpoint="https://os.example.com",
        embedding_client_factory=fake_embed_client,
        search_client_factory=fake_search_client,
    )
    results = retriever.retrieve(question="What was decided?", meeting_id="mtg_123", tenant_id="tenant_123", top_k=5)

    assert len(embed_calls) == 1
    assert len(search_calls) == 1
    assert len(results) == 1
    assert results[0].chunk_id == "chunk_001"
    assert results[0].score == 0.95
