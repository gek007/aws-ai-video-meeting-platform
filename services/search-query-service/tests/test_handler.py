import json

from search_query_service.handler import lambda_handler
from search_query_service.service import SearchQueryService
from search_query_service.store import InMemorySearchStore
from shared.responses import json_response


def _store():
    meetings = [{"meetingId": "mtg_001", "tenantId": "tenant_demo", "title": "Budget Planning"}]
    topics = [
        {"meetingId": "mtg_001", "tenantId": "tenant_demo", "label": "budget"},
        {"meetingId": "mtg_002", "tenantId": "tenant_demo", "label": "budget"},
    ]
    return InMemorySearchStore(meetings=meetings, topics=topics)


def _handler_with_store(event):
    store = _store()
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


def test_handler_search_action():
    response = _handler_with_store({"action": "search", "query": "budget", "tenantId": "tenant_demo"})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["result"]["query"] == "budget"
    assert body["result"]["results"][0]["meetingId"] == "mtg_001"


def test_handler_related_action():
    response = _handler_with_store({"action": "related", "meetingId": "mtg_001", "tenantId": "tenant_demo"})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["result"]["meetingId"] == "mtg_001"


def test_handler_defaults_to_related_when_no_action():
    response = _handler_with_store({"meetingId": "mtg_001"})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["result"]["meetingId"] == "mtg_001"


def test_handler_no_store_returns_empty_results():
    response = lambda_handler({"action": "search", "query": "budget"}, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["result"]["results"] == []
