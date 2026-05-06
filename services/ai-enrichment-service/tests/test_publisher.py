import json

from ai_enrichment_service.publisher import SNSTopicPublisher


class StubSNSClient:
    def __init__(self) -> None:
        self.messages = []

    def publish(self, TopicArn: str, Message: str, Subject: str) -> None:
        self.messages.append({"TopicArn": TopicArn, "Message": Message, "Subject": Subject})


def test_sns_topic_publisher_publishes_meeting_intelligence_event():
    client = StubSNSClient()
    publisher = SNSTopicPublisher(
        topic_arn="arn:aws:sns:us-east-1:123456789012:meeting-intelligence",
        sns_client=client,
    )

    publisher.publish_meeting_intelligence({"eventType": "meeting.intelligence.generated", "meetingId": "mtg_123"})

    assert client.messages[0]["TopicArn"].endswith(":meeting-intelligence")
    assert client.messages[0]["Subject"] == "meeting.intelligence.generated"
    assert json.loads(client.messages[0]["Message"])["eventType"] == "meeting.intelligence.generated"
