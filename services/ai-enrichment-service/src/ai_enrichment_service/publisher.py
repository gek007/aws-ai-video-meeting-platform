from __future__ import annotations

import json
import os
from dataclasses import dataclass, field


@dataclass(slots=True)
class InMemoryTopicPublisher:
    messages: list[dict] = field(default_factory=list)

    def publish_meeting_intelligence(self, payload: dict) -> None:
        self.messages.append(payload)


class SNSTopicPublisher:
    def __init__(self, topic_arn: str | None = None, sns_client=None) -> None:
        self._topic_arn = topic_arn or os.environ["MEETING_INTELLIGENCE_TOPIC_ARN"]
        if sns_client is not None:
            self._sns_client = sns_client
        else:
            import boto3

            self._sns_client = boto3.client("sns")

    def publish_meeting_intelligence(self, payload: dict) -> None:
        self._sns_client.publish(
            TopicArn=self._topic_arn,
            Message=json.dumps(payload),
            Subject="meeting.intelligence.generated",
        )
