from __future__ import annotations

from search_query_service.service import SearchQueryService
from shared.responses import json_response


def lambda_handler(event: dict, _context) -> dict:
    result = SearchQueryService().related_meetings(event.get("meetingId", "mtg_unknown"))
    return json_response(200, {"message": "Related meetings fetched.", "result": result})

