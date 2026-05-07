from __future__ import annotations

import json
import os
from dataclasses import dataclass, field


@dataclass(slots=True)
class InMemoryQueuePublisher:
    messages: list[dict] = field(default_factory=list)

    def publish_ai_enrichment(self, payload: dict) -> None:
        self.messages.append(payload)


class SQSQueuePublisher:
    def __init__(self, queue_url: str | None = None, sqs_client=None) -> None:
        self._queue_url = queue_url or os.environ["AI_ENRICHMENT_QUEUE_URL"]
        if sqs_client is not None:
            self._sqs_client = sqs_client
        else:
            import boto3

            self._sqs_client = boto3.client("sqs")

    def publish_ai_enrichment(self, payload: dict) -> None:
        self._sqs_client.send_message(
            QueueUrl=self._queue_url,
            MessageBody=json.dumps(payload),
        )
