from __future__ import annotations

from typing import Protocol

from connectors.issues import GitHubIssuesConnector, IssueConnector, JiraConnector


class MetadataStore(Protocol):
    def record_external_task(
        self,
        *,
        tenant_id: str,
        action_item_id: str,
        provider: str,
        external_id: str,
        external_url: str,
        status: str,
    ) -> None: ...


class IntegrationService:
    def __init__(self, connector: IssueConnector | None = None, metadata_store: MetadataStore | None = None) -> None:
        self._connector = connector or IssueConnector()
        self._metadata_store = metadata_store

    def create_external_task(self, event: dict) -> dict:
        item = event["items"][0]
        provider = event.get("provider", "jira")
        connector = self._resolve_connector(provider)
        created = connector.create_issue(
            provider=provider,
            title=item["title"],
            description=item.get("description", ""),
        )
        if self._metadata_store is not None:
            self._metadata_store.record_external_task(
                tenant_id=event.get("tenantId", "tenant_demo"),
                action_item_id=item["actionItemId"],
                provider=created.provider,
                external_id=created.external_id,
                external_url=created.external_url,
                status=created.status,
            )
        return {
            "eventType": "external.task.created",
            "actionItemId": item["actionItemId"],
            "provider": created.provider,
            "externalId": created.external_id,
            "externalUrl": created.external_url,
            "status": created.status,
        }

    def _resolve_connector(self, provider: str) -> IssueConnector:
        if provider == "jira":
            return JiraConnector()
        if provider == "github":
            return GitHubIssuesConnector()
        return self._connector
