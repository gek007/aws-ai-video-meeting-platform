import json

from chat_rag_service.answerer import INSUFFICIENT_INFORMATION
from chat_rag_service.handler import lambda_handler


def test_chat_handler_returns_200():
    response = lambda_handler({"meetingId": "mtg_123", "question": "What was decided?"}, None)
    assert response["statusCode"] == 200


def test_chat_handler_returns_insufficient_when_no_chunks_in_store():
    response = lambda_handler({"meetingId": "mtg_123", "question": "What was decided?"}, None)
    result = json.loads(response["body"])["result"]
    assert result["answer"] == INSUFFICIENT_INFORMATION
    assert result["citations"] == []
    assert result["confidence"] == "low"


def test_chat_handler_passes_question_and_meeting_through():
    response = lambda_handler(
        {"meetingId": "mtg_abc", "question": "Who owns the action items?", "tenantId": "tenant_x"},
        None,
    )
    result = json.loads(response["body"])["result"]
    assert result["meetingId"] == "mtg_abc"
    assert result["question"] == "Who owns the action items?"
