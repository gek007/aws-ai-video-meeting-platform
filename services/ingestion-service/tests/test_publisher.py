import json

from ingestion_service.publisher import SQSQueuePublisher


class StubSQSClient:
    def __init__(self) -> None:
        self.messages = []

    def send_message(self, QueueUrl: str, MessageBody: str) -> None:
        self.messages.append({"QueueUrl": QueueUrl, "MessageBody": MessageBody})


def test_sqs_queue_publisher_sends_message_to_media_processing_queue():
    client = StubSQSClient()
    publisher = SQSQueuePublisher(queue_url="https://sqs.example/media-processing", sqs_client=client)

    publisher.publish_media_processing({"eventType": "media.processing.requested", "meetingId": "mtg_123"})

    assert client.messages[0]["QueueUrl"] == "https://sqs.example/media-processing"
    assert json.loads(client.messages[0]["MessageBody"])["eventType"] == "media.processing.requested"
