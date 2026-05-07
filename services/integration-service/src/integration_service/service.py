from __future__ import annotations

from typing import Callable, Protocol

from connectors.issues import GitHubIssuesConnector, IssueConnector, JiraConnector


class MetadataStore(Protocol):
    def find_existing_task(
        self,
        *,
        action_item_id: str,
        provider: str,
        provider_project_key: str,
    ) -> dict | None: ...

    def record_external_task(
        self,
        *,
        tenant_id: str,
        action_item_id: str,
        provider: str,
        provider_project_key: str,
        external_id: str,
        external_url: str,
        status: str,
    ) -> None: ...


class IntegrationService:
    def __init__(
        self,
        metadata_store: MetadataStore | None = None,
        connector_factory: Callable[[str], IssueConnector] | None = None,
    ) -> None:
        self._metadata_store = metadata_store
        self._connector_factory = connector_factory or self._default_connector_factory

    def create_external_task(self, event: dict) -> dict:
        item = event["items"][0]
        provider = event.get("provider", "jira")
        provider_project_key = event.get("providerProjectKey", "")
        action_item_id = item["actionItemId"]
        tenant_id = event.get("tenantId", "tenant_demo")

        if self._metadata_store is not None:
            existing = self._metadata_store.find_existing_task(
                action_item_id=action_item_id,
                provider=provider,
                provider_project_key=provider_project_key,
            )
            if existing is not None:
                return {
                    "eventType": "external.task.exists",
                    "actionItemId": action_item_id,
                    "provider": provider,
                    "externalId": existing["externalId"],
                    "externalUrl": existing["externalUrl"],
                    "status": existing["status"],
                    "duplicate": True,
                }

        connector = self._connector_factory(provider)
        created = connector.create_issue(
            provider=provider,
            title=item["title"],
            description=item.get("description", ""),
        )

        if self._metadata_store is not None:
            self._metadata_store.record_external_task(
                tenant_id=tenant_id,
                action_item_id=action_item_id,
                provider=created.provider,
                provider_project_key=provider_project_key,
                external_id=created.external_id,
                external_url=created.external_url,
                status=created.status,
            )

        return {
            "eventType": "external.task.created",
            "actionItemId": action_item_id,
            "provider": created.provider,
            "externalId": created.external_id,
            "externalUrl": created.external_url,
            "status": created.status,
            "duplicate": False,
        }

    @staticmethod
    def _default_connector_factory(provider: str) -> IssueConnector:
        if provider == "jira":
            return JiraConnector()
        if provider == "github":
            return GitHubIssuesConnector()
        return IssueConnector()
