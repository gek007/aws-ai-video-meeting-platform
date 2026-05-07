import pytest
from ai_enrichment_service.embedder import BedrockEmbeddingGenerator, InMemoryEmbeddingGenerator


def _sample_chunks():
    return [
        {"chunkIndex": 0, "chunkText": "Hello world this is the first chunk."},
        {"chunkIndex": 1, "chunkText": "Second chunk discusses authentication."},
    ]


def test_in_memory_generator_returns_one_embedding_per_chunk():
    generator = InMemoryEmbeddingGenerator()
    result = generator.generate_batch(_sample_chunks())
    assert len(result) == 2
    assert result[0].chunk_index == 0
    assert result[1].chunk_index == 1


def test_in_memory_generator_produces_deterministic_refs():
    generator = InMemoryEmbeddingGenerator()
    result = generator.generate_batch(_sample_chunks())
    assert result[0].embedding_ref == "emb_inmemory_000"
    assert result[1].embedding_ref == "emb_inmemory_001"


def test_in_memory_generator_produces_non_empty_vectors():
    generator = InMemoryEmbeddingGenerator()
    result = generator.generate_batch(_sample_chunks())
    assert all(isinstance(v, float) for v in result[0].vector)
    assert len(result[0].vector) > 0


def test_bedrock_generator_calls_model_per_chunk():
    calls = []

    def fake_client():
        import io, json

        class _Client:
            def invoke_model(self, **kwargs):
                calls.append(kwargs)
                vector = [0.1] * 1536
                return {"body": io.BytesIO(json.dumps({"embedding": vector}).encode())}

        return _Client()

    generator = BedrockEmbeddingGenerator(model_id="amazon.titan-embed-text-v1", client_factory=fake_client)
    chunks = _sample_chunks()
    result = generator.generate_batch(chunks)

    assert len(result) == 2
    assert len(calls) == 2
    assert result[0].vector == [0.1] * 1536
    assert result[0].embedding_ref == "emb_bedrock_000"
