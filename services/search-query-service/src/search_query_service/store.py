from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable


@dataclass(slots=True)
class InMemorySearchStore:
    """Seeded in-memory store for tests."""

    meetings: list[dict] = field(default_factory=list)
    topics: list[dict] = field(default_factory=list)

    def search_meetings(self, *, tenant_id: str, query: str, limit: int = 20) -> list[dict]:
        q = query.lower()
        results = []
        for m in self.meetings:
            if m.get("tenantId") != tenant_id:
                continue
            title = m.get("title", "").lower()
            if q in title:
                results.append({**m, "score": 1.0, "matchType": "title"})
        return results[:limit]

    def related_meetings(self, *, tenant_id: str, meeting_id: str, limit: int = 10) -> list[dict]:
        source_topics = {
            t["label"]
            for t in self.topics
            if t.get("meetingId") == meeting_id and t.get("tenantId") == tenant_id
        }
        if not source_topics:
            return []

        score_map: dict[str, float] = {}
        for t in self.topics:
            if t.get("tenantId") != tenant_id:
                continue
            if t.get("meetingId") == meeting_id:
                continue
            if t["label"] in source_topics:
                mid = t["meetingId"]
                score_map[mid] = score_map.get(mid, 0.0) + 1.0

        return sorted(
            [{"meetingId": mid, "score": score / len(source_topics)} for mid, score in score_map.items()],
            key=lambda x: x["score"],
            reverse=True,
        )[:limit]


class AuroraSearchStore:
    def __init__(self, dsn: str | None = None, connection_factory: Callable[[], object] | None = None) -> None:
        self._dsn = dsn or os.getenv("AURORA_DATABASE_URL") or os.getenv("DATABASE_URL")
        if not self._dsn and connection_factory is None:
            raise ValueError("AURORA_DATABASE_URL or DATABASE_URL is required for AuroraSearchStore.")
        self._connection_factory = connection_factory

    def search_meetings(self, *, tenant_id: str, query: str, limit: int = 20) -> list[dict]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, title, status, recorded_at
                    FROM meetings
                    WHERE tenant_id = %s
                      AND (
                            title ILIKE %s
                         OR EXISTS (
                              SELECT 1 FROM summaries s
                              WHERE s.meeting_id = meetings.id
                                AND s.content ILIKE %s
                            )
                      )
                    ORDER BY recorded_at DESC NULLS LAST
                    LIMIT %s
                    """,
                    (tenant_id, f"%{query}%", f"%{query}%", limit),
                )
                rows = cur.fetchall()
                return [
                    {
                        "meetingId": row[0],
                        "title": row[1],
                        "status": row[2],
                        "recordedAt": str(row[3]) if row[3] else None,
                        "score": 1.0,
                        "matchType": "metadata",
                    }
                    for row in rows
                ]

    def related_meetings(self, *, tenant_id: str, meeting_id: str, limit: int = 10) -> list[dict]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT other.meeting_id,
                           COUNT(*) AS shared_topics,
                           COUNT(*)::float / NULLIF(
                               (SELECT COUNT(*) FROM topics WHERE meeting_id = %s AND tenant_id = %s), 0
                           ) AS score
                    FROM topics source
                    JOIN topics other
                      ON other.label = source.label
                     AND other.tenant_id = %s
                     AND other.meeting_id != %s
                    WHERE source.meeting_id = %s
                      AND source.tenant_id = %s
                    GROUP BY other.meeting_id
                    ORDER BY score DESC
                    LIMIT %s
                    """,
                    (meeting_id, tenant_id, tenant_id, meeting_id, meeting_id, tenant_id, limit),
                )
                rows = cur.fetchall()
                return [
                    {"meetingId": row[0], "sharedTopics": row[1], "score": float(row[2] or 0)}
                    for row in rows
                ]

    def _connect(self):
        if self._connection_factory is not None:
            return self._connection_factory()
        import psycopg
        return psycopg.connect(self._dsn)
