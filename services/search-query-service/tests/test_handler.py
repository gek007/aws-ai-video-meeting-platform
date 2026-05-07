import json

from search_query_service.handler import lambda_handler


def test_search_handler_returns_related_results():
    response = lambda_handler({"meetingId": "mtg_123"}, None)
    body = json.loads(response["body"])
    assert body["result"]["meetingId"] == "mtg_123"
