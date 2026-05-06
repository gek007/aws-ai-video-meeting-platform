from search_query_service.handler import lambda_handler


def test_search_handler_returns_related_results():
    response = lambda_handler({"meetingId": "mtg_123"}, None)
    assert response["body"]["result"]["meetingId"] == "mtg_123"

