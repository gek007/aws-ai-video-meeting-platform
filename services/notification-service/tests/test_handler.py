import json

from notification_service.handler import lambda_handler


def test_notification_handler_returns_sent_event():
    response = lambda_handler({"recipient": "user@example.com"}, None)
    body = json.loads(response["body"])
    assert body["result"]["eventType"] == "notification.sent"
    assert body["result"]["provider"] == "in-memory"
    assert body["result"]["status"] == "sent"
