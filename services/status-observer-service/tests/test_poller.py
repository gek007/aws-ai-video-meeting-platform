import pytest
from status_observer_service.poller import (
    ExternalTaskStatus,
    GitHubStatusPoller,
    InMemoryStatusPoller,
    JiraStatusPoller,
)


def test_in_memory_poller_returns_configured_status():
    poller = InMemoryStatusPoller(status_map={"JIRA-123": "DONE", "JIRA-456": "IN_PROGRESS"})
    result = poller.poll(provider="jira", external_id="JIRA-123", config={})
    assert result.status == "DONE"
    assert result.external_id == "JIRA-123"
    assert result.provider == "jira"


def test_in_memory_poller_defaults_to_open_for_unknown():
    poller = InMemoryStatusPoller()
    result = poller.poll(provider="jira", external_id="UNKNOWN-999", config={})
    assert result.status == "OPEN"


def test_jira_poller_raises_without_base_url():
    with pytest.raises(ValueError, match="JIRA_BASE_URL"):
        JiraStatusPoller()


def test_jira_poller_fetches_status():
    import json

    calls = []

    def fake_session_factory(api_token, user_email):
        class _Response:
            def raise_for_status(self):
                pass
            def json(self):
                return {"fields": {"status": {"name": "Done"}}}

        class _Session:
            def get(self, url, **kwargs):
                calls.append({"url": url, "headers": kwargs.get("headers", {})})
                return _Response()

        return _Session()

    poller = JiraStatusPoller(base_url="https://jira.example.com", client_factory=fake_session_factory)
    result = poller.poll(provider="jira", external_id="PROJ-42", config={"apiToken": "tok", "userEmail": "u@x.com"})

    assert result.status == "Done"
    assert result.external_id == "PROJ-42"
    assert "PROJ-42" in calls[0]["url"]


def test_github_poller_fetches_state():
    calls = []

    def fake_session_factory(token):
        class _Response:
            def raise_for_status(self):
                pass
            def json(self):
                return {"state": "closed"}

        class _Session:
            def get(self, url, **kwargs):
                calls.append(url)
                return _Response()

        return _Session()

    poller = GitHubStatusPoller(client_factory=fake_session_factory)
    result = poller.poll(
        provider="github",
        external_id="42",
        config={"token": "ghp_abc", "owner": "myorg", "repo": "myrepo"},
    )

    assert result.status == "CLOSED"
    assert result.provider == "github"
    assert "myorg/myrepo/issues/42" in calls[0]
