from __future__ import annotations

from connectors.issues import GitHubIssuesConnector, IssueConnector, JiraConnector


class IntegrationService:
    def __init__(self, connector: IssueConnector | None = None) -> None:
        self._connector = connector or IssueConnector()

    def create_external_task(self, event: dict) -> dict:
        item = event["items"][0]
        provider = event.get("provider", "jira")
        connector = self._resolve_connector(provider)
        created = connector.create_issue(
            provider=provider,
            title=item["title"],
            description=item.get("description", ""),
        )
        return {
            "eventType": "external.task.created",
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
