from notification_service.handler import lambda_handler


def test_notification_handler_returns_sent_event():
    response = lambda_handler({"recipient": "user@example.com"}, None)
    assert response["body"]["result"]["eventType"] == "notification.sent"
    assert response["body"]["result"]["provider"] == "in-memory"
    assert response["body"]["result"]["status"] == "sent"
