from __future__ import annotations

import os

from shared.responses import json_response
from status_observer_service.poller import GitHubStatusPoller, InMemoryStatusPoller, JiraStatusPoller
from status_observer_service.store import AuroraStatusObserverStore, InMemoryMetadataStore
from status_observer_service.service import StatusObserverService


def lambda_handler(event: dict, _context) -> dict:
    metadata_store = _build_metadata_store()
    poller = _build_poller(event)
    notification_publisher = _build_notification_publisher()
    result = StatusObserverService(
        metadata_store=metadata_store,
        poller=poller,
        notification_publisher=notification_publisher,
    ).sync(event)
    return json_response(200, {"message": "Status sync processed.", "result": result})


def _build_metadata_store():
    if os.getenv("AURORA_DATABASE_URL") or os.getenv("DATABASE_URL"):
        return AuroraStatusObserverStore()
    return InMemoryMetadataStore()


def _build_poller(event: dict):
    provider = event.get("provider", "")
    if provider == "jira" and os.getenv("JIRA_BASE_URL"):
        return JiraStatusPoller()
    if provider == "github" and os.getenv("GITHUB_TOKEN"):
        return GitHubStatusPoller()
    return None


def _build_notification_publisher():
    queue_url = os.getenv("NOTIFICATIONS_QUEUE_URL")
    if queue_url:
        return _SQSNotificationPublisher(queue_url)
    return None


class _SQSNotificationPublisher:
    def __init__(self, queue_url: str) -> None:
        self._queue_url = queue_url

    def publish_status_change(self, payload: dict) -> None:
        import json
        import boto3
        boto3.client("sqs").send_message(
            QueueUrl=self._queue_url,
            MessageBody=json.dumps(payload),
        )
