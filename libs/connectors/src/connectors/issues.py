from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CreatedIssue:
    provider: str
    external_id: str
    external_url: str
    status: str


class IssueConnector:
    def create_issue(self, *, provider: str, title: str, description: str) -> CreatedIssue:
        slug = title.lower().replace(" ", "-")[:24]
        return CreatedIssue(
            provider=provider,
            external_id=f"{provider}-001",
            external_url=f"https://example.com/{provider}/{slug}",
            status="OPEN",
        )


class JiraConnector(IssueConnector):
    def create_issue(self, *, provider: str, title: str, description: str) -> CreatedIssue:
        created = super().create_issue(provider="jira", title=title, description=description)
        return CreatedIssue(
            provider=created.provider,
            external_id="JIRA-101",
            external_url=f"https://jira.example.com/browse/{created.external_id}",
            status=created.status,
        )


class GitHubIssuesConnector(IssueConnector):
    def create_issue(self, *, provider: str, title: str, description: str) -> CreatedIssue:
        created = super().create_issue(provider="github", title=title, description=description)
        return CreatedIssue(
            provider=created.provider,
            external_id="GH-101",
            external_url="https://github.com/example/repo/issues/101",
            status=created.status,
        )
