import json

from media_service.publisher import SQSQueuePublisher


class StubSQSClient:
    def __init__(self) -> None:
        self.messages = []

    def send_message(self, QueueUrl: str, MessageBody: str) -> None:
        self.messages.append({"QueueUrl": QueueUrl, "MessageBody": MessageBody})


def test_sqs_queue_publisher_sends_message_to_transcription_queue():
    client = StubSQSClient()
    publisher = SQSQueuePublisher(queue_url="https://sqs.example/transcription", sqs_client=client)

    publisher.publish_transcription_request({"eventType": "transcription.requested", "meetingId": "mtg_123"})

    assert client.messages[0]["QueueUrl"] == "https://sqs.example/transcription"
    assert json.loads(client.messages[0]["MessageBody"])["eventType"] == "transcription.requested"
