from __future__ import annotations

from typing import Protocol


class SearchStore(Protocol):
    def search_meetings(self, *, tenant_id: str, query: str, limit: int) -> list[dict]: ...
    def related_meetings(self, *, tenant_id: str, meeting_id: str, limit: int) -> list[dict]: ...


class SearchQueryService:
    def __init__(self, store: SearchStore | None = None) -> None:
        self._store = store

    def search_meetings(self, *, tenant_id: str, query: str, limit: int = 20) -> dict:
        if self._store is None:
            return {"query": query, "results": []}
        results = self._store.search_meetings(tenant_id=tenant_id, query=query, limit=limit)
        return {"query": query, "results": results}

    def related_meetings(self, *, tenant_id: str, meeting_id: str, limit: int = 10) -> dict:
        if self._store is None:
            return {"meetingId": meeting_id, "results": []}
        results = self._store.related_meetings(tenant_id=tenant_id, meeting_id=meeting_id, limit=limit)
        return {"meetingId": meeting_id, "results": results}
