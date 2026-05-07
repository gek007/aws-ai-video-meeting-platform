from __future__ import annotations

from dataclasses import asdict
from typing import Protocol

from contracts.pipeline import ActionItem
from contracts.validation import require_keys
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


class AIEnrichmentService:
    PROMPT_VERSION = "v1"

    def __init__(self, publisher: TopicPublisher, metadata_store: MetadataStore) -> None:
        self._publisher = publisher
        self._metadata_store = metadata_store

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
        action_item = ActionItem(
            title="Fix login timeout issue",
            description="Investigate and resolve intermittent login timeout failures.",
            item_type="bug",
            owner_email="owner@example.com",
            priority="high",
        )
        next_event = base_event(
            "meeting.intelligence.generated",
            tenant_id=event["tenantId"],
            meeting_id=event["meetingId"],
            video_item_id=event["videoItemId"],
            correlation_id=event["correlationId"],
        )
        next_event["summary"] = "Meeting summary placeholder."
        next_event["topics"] = ["authentication", "reliability"]
        persisted_action_item = asdict(action_item)
        persisted_action_item["actionItemId"] = new_id("act")
        next_event["actionItems"] = [persisted_action_item]
        next_event["taskProvider"] = event.get("taskProvider", "jira")
        next_event["promptVersion"] = self.PROMPT_VERSION
        next_event["transcriptChunks"] = chunks
        next_event["embeddings"] = [chunk["embeddingRef"] for chunk in chunks]
        next_event["decisions"] = [{"description": "Prioritize timeout fix", "owner": "owner@example.com"}]
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
