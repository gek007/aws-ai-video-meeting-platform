from search_query_service.service import SearchQueryService


def test_search_query_service_returns_related_meeting_result():
    result = SearchQueryService().related_meetings("mtg_123")

    assert result["meetingId"] == "mtg_123"
    assert result["results"][0]["meetingId"] == "mtg_related_001"
    assert result["results"][0]["score"] == 0.92

