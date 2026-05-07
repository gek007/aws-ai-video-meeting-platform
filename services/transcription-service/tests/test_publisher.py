import json

from transcription_service.publisher import SQSQueuePublisher


class StubSQSClient:
    def __init__(self) -> None:
        self.messages = []

    def send_message(self, QueueUrl: str, MessageBody: str) -> None:
        self.messages.append({"QueueUrl": QueueUrl, "MessageBody": MessageBody})


def test_sqs_queue_publisher_sends_message_to_ai_enrichment_queue():
    client = StubSQSClient()
    publisher = SQSQueuePublisher(queue_url="https://sqs.example/ai-enrichment", sqs_client=client)

    publisher.publish_ai_enrichment({"eventType": "meeting.transcript.ready", "meetingId": "mtg_123"})

    assert client.messages[0]["QueueUrl"] == "https://sqs.example/ai-enrichment"
    assert json.loads(client.messages[0]["MessageBody"])["eventType"] == "meeting.transcript.ready"

