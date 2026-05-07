from search_query_service.service import SearchQueryService
from search_query_service.store import InMemorySearchStore


def _store():
    meetings = [
        {"meetingId": "mtg_001", "tenantId": "t1", "title": "Q1 Budget Planning"},
        {"meetingId": "mtg_002", "tenantId": "t1", "title": "Auth Review"},
    ]
    topics = [
        {"meetingId": "mtg_001", "tenantId": "t1", "label": "budget"},
        {"meetingId": "mtg_002", "tenantId": "t1", "label": "budget"},
    ]
    return InMemorySearchStore(meetings=meetings, topics=topics)


def test_search_meetings_returns_matching_results():
    service = SearchQueryService(store=_store())
    result = service.search_meetings(tenant_id="t1", query="budget")
    assert result["query"] == "budget"
    assert result["results"][0]["meetingId"] == "mtg_001"


def test_search_meetings_returns_empty_results_without_store():
    service = SearchQueryService(store=None)
    result = service.search_meetings(tenant_id="t1", query="budget")
    assert result["results"] == []


def test_related_meetings_returns_results():
    service = SearchQueryService(store=_store())
    result = service.related_meetings(tenant_id="t1", meeting_id="mtg_001")
    assert result["meetingId"] == "mtg_001"
    assert result["results"][0]["meetingId"] == "mtg_002"


def test_related_meetings_returns_empty_without_store():
    service = SearchQueryService(store=None)
    result = service.related_meetings(tenant_id="t1", meeting_id="mtg_001")
    assert result["meetingId"] == "mtg_001"
    assert result["results"] == []
