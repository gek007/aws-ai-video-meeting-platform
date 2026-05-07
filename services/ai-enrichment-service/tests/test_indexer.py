import pytest
from ai_enrichment_service.embedder import Embedding, InMemoryEmbeddingGenerator
from ai_enrichment_service.indexer import InMemoryVectorIndexer, OpenSearchVectorIndexer


def _chunks():
    return [
        {"chunkIndex": 0, "chunkText": "First chunk content."},
        {"chunkIndex": 1, "chunkText": "Second chunk content."},
    ]


def _embeddings():
    return [
        Embedding(chunk_index=0, vector=[0.1, 0.2], embedding_ref="emb_000"),
        Embedding(chunk_index=1, vector=[0.3, 0.4], embedding_ref="emb_001"),
    ]


def test_in_memory_indexer_stores_all_chunks():
    indexer = InMemoryVectorIndexer()
    doc_ids = indexer.index_chunks(
        tenant_id="tenant_123",
        meeting_id="mtg_123",
        video_item_id="vid_123",
        chunks=_chunks(),
        embeddings=_embeddings(),
    )
    assert len(doc_ids) == 2
    assert doc_ids[0] == "emb_000"
    assert doc_ids[1] == "emb_001"
    assert len(indexer.documents) == 2
    assert indexer.documents[0]["vector"] == [0.1, 0.2]
    assert indexer.documents[0]["meetingId"] == "mtg_123"


def test_in_memory_indexer_includes_tenant_and_meeting_metadata():
    indexer = InMemoryVectorIndexer()
    indexer.index_chunks(
        tenant_id="tenant_abc",
        meeting_id="mtg_xyz",
        video_item_id="vid_qrs",
        chunks=_chunks(),
        embeddings=_embeddings(),
    )
    for doc in indexer.documents:
        assert doc["tenantId"] == "tenant_abc"
        assert doc["meetingId"] == "mtg_xyz"


def test_opensearch_indexer_raises_without_endpoint():
    with pytest.raises(ValueError, match="OPENSEARCH_ENDPOINT"):
        OpenSearchVectorIndexer()


def test_opensearch_indexer_calls_client_index_per_chunk():
    indexed = []

    def fake_client():
        class _Client:
            def index(self, **kwargs):
                indexed.append(kwargs)
        return _Client()

    indexer = OpenSearchVectorIndexer(endpoint="https://os.example.com", client_factory=fake_client)
    doc_ids = indexer.index_chunks(
        tenant_id="tenant_123",
        meeting_id="mtg_123",
        video_item_id="vid_123",
        chunks=_chunks(),
        embeddings=_embeddings(),
    )
    assert len(indexed) == 2
    assert indexed[0]["id"] == "emb_000"
    assert indexed[0]["body"]["chunkText"] == "First chunk content."
    assert indexed[0]["body"]["chunkVector"] == [0.1, 0.2]
    assert doc_ids == ["emb_000", "emb_001"]
