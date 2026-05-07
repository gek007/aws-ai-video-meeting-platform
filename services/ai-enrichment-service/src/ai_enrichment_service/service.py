from __future__ import annotations

from typing import Protocol

from contracts.validation import require_keys
from ai_enrichment_service.embedder import Embedding
from ai_enrichment_service.generator import EnrichmentOutput
from shared.events import base_event
from shared.ids import new_id


class TopicPublisher(Protocol):
    def publish_meeting_intelligence(self, payload: dict) -> None: ...


class MetadataStore(Protocol):
    def persist_enrichment(
        self,
        *,
        tenant_id: str,
        meeting_id: str,
        video_item_id: str,
        summary: str,
        topics: list[str],
        decisions: list[dict],
        action_items: list[dict],
        transcript_chunks: list[dict],
        prompt_version: str,
    ) -> None: ...


class EnrichmentGenerator(Protocol):
    def generate(self, *, transcript_text: str) -> EnrichmentOutput: ...


class EmbeddingGenerator(Protocol):
    def generate_batch(self, chunks: list[dict]) -> list[Embedding]: ...


class VectorIndexer(Protocol):
    def index_chunks(
        self,
        *,
        tenant_id: str,
        meeting_id: str,
        video_item_id: str,
        chunks: list[dict],
        embeddings: list[Embedding],
    ) -> list[str]: ...


class AIEnrichmentService:
    PROMPT_VERSION = "v1"

    def __init__(
        self,
        publisher: TopicPublisher,
        metadata_store: MetadataStore,
        generator: EnrichmentGenerator,
        embedding_generator: EmbeddingGenerator | None = None,
        vector_indexer: VectorIndexer | None = None,
    ) -> None:
        self._publisher = publisher
        self._metadata_store = metadata_store
        self._generator = generator
        self._embedding_generator = embedding_generator
        self._vector_indexer = vector_indexer

    def chunk_transcript(self, transcript_text: str, chunk_size: int = 120) -> list[dict]:
        words = transcript_text.split()
        chunks: list[dict] = []
        for index in range(0, len(words), chunk_size):
            slice_words = words[index : index + chunk_size]
            chunks.append(
                {
                    "chunkIndex": len(chunks),
                    "chunkText": " ".join(slice_words),
                    "embeddingRef": f"emb_{len(chunks):03d}",
                }
            )
        return chunks

    def validate_output(self, payload: dict) -> None:
        require_keys(payload, ["summary", "topics", "actionItems"])

    def enrich(self, event: dict) -> dict:
        transcript_text = event.get(
            "transcriptText",
            "Authentication issue discussion with decisions and action items.",
        )
        chunks = self.chunk_transcript(transcript_text)
        generated = self._generator.generate(transcript_text=transcript_text)
        next_event = base_event(
            "meeting.intelligence.generated",
            tenant_id=event["tenantId"],
            meeting_id=event["meetingId"],
            video_item_id=event["videoItemId"],
            correlation_id=event["correlationId"],
        )
        embeddings = (
            self._embedding_generator.generate_batch(chunks)
            if self._embedding_generator is not None
            else []
        )
        embedding_refs = self._index_embeddings(
            event=event,
            chunks=chunks,
            embeddings=embeddings,
        )
        for chunk, ref in zip(chunks, embedding_refs or [chunk["embeddingRef"] for chunk in chunks]):
            chunk["embeddingRef"] = ref

        next_event["summary"] = generated.summary
        next_event["topics"] = generated.topics
        next_event["actionItems"] = self._normalize_action_items(generated.action_items)
        next_event["taskProvider"] = event.get("taskProvider", "jira")
        next_event["promptVersion"] = self.PROMPT_VERSION
        next_event["modelId"] = generated.model_id
        next_event["transcriptChunks"] = chunks
        next_event["embeddings"] = [chunk["embeddingRef"] for chunk in chunks]
        next_event["decisions"] = generated.decisions
        self.validate_output(next_event)
        self._metadata_store.persist_enrichment(
            tenant_id=event["tenantId"],
            meeting_id=event["meetingId"],
            video_item_id=event["videoItemId"],
            summary=next_event["summary"],
            topics=next_event["topics"],
            decisions=next_event["decisions"],
            action_items=next_event["actionItems"],
            transcript_chunks=next_event["transcriptChunks"],
            prompt_version=self.PROMPT_VERSION,
        )
        self._publisher.publish_meeting_intelligence(next_event)
        return next_event

    def _index_embeddings(self, *, event: dict, chunks: list[dict], embeddings: list) -> list[str] | None:
        if not self._vector_indexer or not embeddings:
            return None
        return self._vector_indexer.index_chunks(
            tenant_id=event["tenantId"],
            meeting_id=event["meetingId"],
            video_item_id=event["videoItemId"],
            chunks=chunks,
            embeddings=embeddings,
        )

    def _normalize_action_items(self, action_items: list[dict]) -> list[dict]:
        normalized = []
        for item in action_items:
            normalized_item = dict(item)
            if "type" in normalized_item and "item_type" not in normalized_item:
                normalized_item["item_type"] = normalized_item.pop("type")
            if "owner" in normalized_item and "owner_email" not in normalized_item:
                normalized_item["owner_email"] = normalized_item.pop("owner")
            normalized_item.setdefault("description", "")
            normalized_item.setdefault("item_type", "todo")
            normalized_item.setdefault("actionItemId", new_id("act"))
            normalized.append(normalized_item)
        return normalized
