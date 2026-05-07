import json

from chat_rag_service.handler import lambda_handler


def test_chat_handler_returns_citations():
    response = lambda_handler({"meetingId": "mtg_123", "question": "What was decided?"}, None)
    body = json.loads(response["body"])
    assert body["result"]["citations"][0]["type"] == "transcript_chunk"
