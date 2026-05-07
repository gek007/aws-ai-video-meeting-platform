from __future__ import annotations

from dataclasses import dataclass, field

from shared.aurora import AuroraBaseStore
from shared.ids import new_id


@dataclass(slots=True)
class InMemoryMetadataStore:
    records: list[dict] = field(default_factory=list)

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
    ) -> None:
        self.records.append(
            {
                "tenantId": tenant_id,
                "meetingId": meeting_id,
                "videoItemId": video_item_id,
                "summary": summary,
                "topics": topics,
                "decisions": decisions,
                "actionItems": action_items,
                "transcriptChunks": transcript_chunks,
                "promptVersion": prompt_version,
                "aiEnrichmentStatus": "completed",
            }
        )


class AuroraAIEnrichmentStore(AuroraBaseStore):
    def __init__(self, dsn: str | None = None, connection_factory=None) -> None:
        super().__init__(dsn, connection_factory, store_name="AuroraAIEnrichmentStore")

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
    ) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM summaries WHERE meeting_id = %s AND summary_type = %s LIMIT 1",
                    (meeting_id, "meeting_summary"),
                )
                if cursor.fetchone() is not None:
                    return

                cursor.execute(
                    """
                    INSERT INTO summaries (id, meeting_id, video_item_id, tenant_id, summary_type, model_id, prompt_version, content)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        new_id("sum"),
                        meeting_id,
                        video_item_id,
                        tenant_id,
                        "meeting_summary",
                        "bedrock-placeholder",
                        prompt_version,
                        summary,
                    ),
                )

                for topic in topics:
                    cursor.execute(
                        """
                        INSERT INTO topics (id, meeting_id, video_item_id, tenant_id, label, start_offset_seconds, end_offset_seconds, confidence_score)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            new_id("top"),
                            meeting_id,
                            video_item_id,
                            tenant_id,
                            topic,
                            0,
                            0,
                            0.90,
                        ),
                    )

                for decision in decisions:
                    cursor.execute(
                        """
                        INSERT INTO decisions (id, meeting_id, video_item_id, tenant_id, description, owner_email)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            new_id("dec"),
                            meeting_id,
                            video_item_id,
                            tenant_id,
                            decision["description"],
                            decision.get("owner"),
                        ),
                    )

                for item in action_items:
                    action_item_id = item.get("actionItemId") or item.get("id") or new_id("act")
                    cursor.execute(
                        """
                        INSERT INTO action_items (
                            id, meeting_id, video_item_id, tenant_id, title, description,
                            item_type, owner_email, priority, status, confidence_score
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                        """,
                        (
                            action_item_id,
                            meeting_id,
                            video_item_id,
                            tenant_id,
                            item["title"],
                            item.get("description"),
                            item["item_type"],
                            item.get("owner_email") or item.get("owner"),
                            item.get("priority"),
                            "open",
                            0.95,
                        ),
                    )

                for chunk in transcript_chunks:
                    cursor.execute(
                        """
                        INSERT INTO transcript_chunks (
                            id, meeting_id, video_item_id, tenant_id, chunk_index,
                            chunk_text, start_offset_seconds, end_offset_seconds, embedding_ref
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            new_id("chk"),
                            meeting_id,
                            video_item_id,
                            tenant_id,
                            chunk["chunkIndex"],
                            chunk["chunkText"],
                            0,
                            0,
                            chunk["embeddingRef"],
                        ),
                    )

                cursor.execute(
                    """
                    UPDATE video_items
                    SET
                        ai_enrichment_status = %s,
                        updated_at = NOW()
                    WHERE id = %s AND tenant_id = %s AND meeting_id = %s
                    """,
                    (
                        "completed",
                        video_item_id,
                        tenant_id,
                        meeting_id,
                    ),
                )
            connection.commit()

