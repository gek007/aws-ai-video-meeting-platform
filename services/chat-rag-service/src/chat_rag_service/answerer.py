from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Callable

from chat_rag_service.retriever import RetrievedChunk


@dataclass(frozen=True, slots=True)
class AnswerResult:
    answer: str
    confidence: str
    citations: list[dict]


INSUFFICIENT_INFORMATION = "Not enough information is available to answer this question from the meeting content."


class InMemoryAnswerer:
    """Deterministic answerer for tests. Builds a response from retrieved chunks directly."""

    def answer(self, *, question: str, chunks: list[RetrievedChunk], context: dict) -> AnswerResult:
        if not chunks:
            return AnswerResult(
                answer=INSUFFICIENT_INFORMATION,
                confidence="low",
                citations=[],
            )
        excerpt = " ".join(c.chunk_text[:100] for c in chunks[:2])
        return AnswerResult(
            answer=f"Based on the meeting content: {excerpt}",
            confidence="high" if len(chunks) >= 3 else "medium",
            citations=[
                {
                    "type": "transcript_chunk",
                    "meetingId": c.meeting_id,
                    "videoItemId": c.video_item_id,
                    "chunkId": c.chunk_id,
                    "startOffsetSeconds": c.start_offset_seconds,
                    "endOffsetSeconds": c.end_offset_seconds,
                }
                for c in chunks
            ],
        )


class BedrockAnswerer:
    """Generates a grounded RAG answer using Amazon Bedrock."""

    SYSTEM_PROMPT = (
        "You are a meeting intelligence assistant. "
        "Answer the user's question using ONLY the meeting context provided. "
        "If the context does not contain enough information, say so. "
        "Always include citations to the specific transcript chunks you used. "
        "Return a JSON object with keys: answer (string), confidence (high|medium|low), "
        "and citations (list of objects with chunkId)."
    )

    def __init__(
        self,
        model_id: str | None = None,
        client_factory: Callable[[], object] | None = None,
    ) -> None:
        self._model_id = model_id or os.getenv("BEDROCK_MODEL_ID")
        if not self._model_id and client_factory is None:
            raise ValueError("BEDROCK_MODEL_ID is required for BedrockAnswerer.")
        self._client_factory = client_factory

    def answer(self, *, question: str, chunks: list[RetrievedChunk], context: dict) -> AnswerResult:
        if not chunks:
            return AnswerResult(answer=INSUFFICIENT_INFORMATION, confidence="low", citations=[])

        context_block = self._build_context(chunks)
        prompt = f"Context:\n{context_block}\n\nQuestion: {question}"
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "temperature": 0,
            "system": self.SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        }
        response = self._client.invoke_model(
            modelId=self._model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )
        payload = json.loads(response["body"].read())
        raw_text = payload["content"][0]["text"]
        try:
            structured = json.loads(raw_text)
        except json.JSONDecodeError:
            structured = {"answer": raw_text, "confidence": "low", "citations": []}

        return AnswerResult(
            answer=structured.get("answer", INSUFFICIENT_INFORMATION),
            confidence=structured.get("confidence", "low"),
            citations=self._resolve_citations(structured.get("citations", []), chunks),
        )

    def _build_context(self, chunks: list[RetrievedChunk]) -> str:
        lines = []
        for chunk in chunks:
            lines.append(f"[{chunk.chunk_id}] {chunk.chunk_text}")
        return "\n\n".join(lines)

    def _resolve_citations(self, raw_citations: list[dict], chunks: list[RetrievedChunk]) -> list[dict]:
        chunk_by_id = {c.chunk_id: c for c in chunks}
        result = []
        for cit in raw_citations:
            chunk_id = cit.get("chunkId", "")
            chunk = chunk_by_id.get(chunk_id)
            entry: dict = {
                "type": "transcript_chunk",
                "chunkId": chunk_id,
            }
            if chunk:
                entry["meetingId"] = chunk.meeting_id
                entry["videoItemId"] = chunk.video_item_id
                entry["startOffsetSeconds"] = chunk.start_offset_seconds
                entry["endOffsetSeconds"] = chunk.end_offset_seconds
            result.append(entry)
        return result

    @property
    def _client(self):
        if self._client_factory is not None:
            return self._client_factory()
        import boto3
        return boto3.client("bedrock-runtime")
