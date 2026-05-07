from __future__ import annotations

import os

from search_query_service.service import SearchQueryService
from search_query_service.store import AuroraSearchStore, InMemorySearchStore
from shared.responses import json_response


def _build_store():
    dsn = os.getenv("AURORA_DATABASE_URL") or os.getenv("DATABASE_URL")
    if dsn:
        return AuroraSearchStore(dsn=dsn)
    return None


def lambda_handler(event: dict, _context) -> dict:
    store = _build_store()
    service = SearchQueryService(store=store)
    tenant_id = event.get("tenantId", "tenant_demo")
    action = event.get("action", "related")

    if action == "search":
        query = event.get("query", "")
        limit = int(event.get("limit", 20))
        result = service.search_meetings(tenant_id=tenant_id, query=query, limit=limit)
        return json_response(200, {"message": "Search complete.", "result": result})

    meeting_id = event.get("meetingId", "mtg_unknown")
    limit = int(event.get("limit", 10))
    result = service.related_meetings(tenant_id=tenant_id, meeting_id=meeting_id, limit=limit)
    return json_response(200, {"message": "Related meetings fetched.", "result": result})
