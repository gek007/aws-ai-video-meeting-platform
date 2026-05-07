import io
import json
import pytest
from chat_rag_service.answerer import BedrockAnswerer, InMemoryAnswerer, INSUFFICIENT_INFORMATION
from chat_rag_service.retriever import RetrievedChunk


def _chunks(n=2):
    return [
        RetrievedChunk(
            chunk_id=f"chunk_{i:03d}",
            meeting_id="mtg_123",
            video_item_id="vid_123",
            chunk_text=f"Chunk {i} content about authentication.",
            score=0.9 - i * 0.05,
            start_offset_seconds=float(i * 30),
            end_offset_seconds=float(i * 30 + 25),
        )
        for i in range(n)
    ]


def test_in_memory_answerer_returns_answer_with_citations():
    answerer = InMemoryAnswerer()
    result = answerer.answer(question="What was decided?", chunks=_chunks(2), context={})

    assert result.answer != INSUFFICIENT_INFORMATION
    assert len(result.citations) == 2
    assert result.citations[0]["type"] == "transcript_chunk"
    assert result.citations[0]["chunkId"] == "chunk_000"
    assert result.confidence in ("high", "medium", "low")


def test_in_memory_answerer_returns_insufficient_when_no_chunks():
    answerer = InMemoryAnswerer()
    result = answerer.answer(question="Q", chunks=[], context={})

    assert result.answer == INSUFFICIENT_INFORMATION
    assert result.confidence == "low"
    assert result.citations == []


def test_in_memory_answerer_high_confidence_with_many_chunks():
    answerer = InMemoryAnswerer()
    result = answerer.answer(question="Q", chunks=_chunks(5), context={})
    assert result.confidence == "high"


def test_bedrock_answerer_raises_without_model_id():
    with pytest.raises(ValueError, match="BEDROCK_MODEL_ID"):
        BedrockAnswerer()


def test_bedrock_answerer_calls_model_and_parses_response():
    calls = []

    structured_response = {
        "answer": "The team decided to fix the login timeout within two weeks.",
        "confidence": "high",
        "citations": [{"chunkId": "chunk_000"}],
    }

    def fake_client():
        class _Client:
            def invoke_model(self, **kwargs):
                calls.append(kwargs)
                payload = {"content": [{"text": json.dumps(structured_response)}]}
                return {"body": io.BytesIO(json.dumps(payload).encode())}
        return _Client()

    answerer = BedrockAnswerer(model_id="anthropic.claude-3-haiku-20240307-v1:0", client_factory=fake_client)
    result = answerer.answer(question="What was decided?", chunks=_chunks(2), context={})

    assert len(calls) == 1
    assert result.answer == structured_response["answer"]
    assert result.confidence == "high"
    assert result.citations[0]["chunkId"] == "chunk_000"
    assert result.citations[0]["meetingId"] == "mtg_123"


def test_bedrock_answerer_handles_non_json_response():
    def fake_client():
        class _Client:
            def invoke_model(self, **kwargs):
                payload = {"content": [{"text": "plain text answer without JSON"}]}
                return {"body": io.BytesIO(json.dumps(payload).encode())}
        return _Client()

    answerer = BedrockAnswerer(model_id="claude-3", client_factory=fake_client)
    result = answerer.answer(question="Q", chunks=_chunks(1), context={})

    assert "plain text answer" in result.answer
    assert result.confidence == "low"


def test_bedrock_answerer_returns_insufficient_when_no_chunks():
    answerer = BedrockAnswerer(model_id="claude-3", client_factory=lambda: None)
    result = answerer.answer(question="Q", chunks=[], context={})
    assert result.answer == INSUFFICIENT_INFORMATION
    assert result.confidence == "low"
