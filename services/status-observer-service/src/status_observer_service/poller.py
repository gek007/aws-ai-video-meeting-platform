from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True, slots=True)
class ExternalTaskStatus:
    external_id: str
    status: str
    provider: str


@dataclass(slots=True)
class InMemoryStatusPoller:
    """Deterministic poller for tests. Returns pre-configured status records."""

    status_map: dict[str, str] = field(default_factory=dict)

    def poll(self, *, provider: str, external_id: str, config: dict) -> ExternalTaskStatus:
        status = self.status_map.get(external_id, "OPEN")
        return ExternalTaskStatus(external_id=external_id, status=status, provider=provider)


class JiraStatusPoller:
    """Fetches the current status of a Jira issue via the REST API."""

    STATUS_FIELD = "status"

    def __init__(
        self,
        base_url: str | None = None,
        client_factory: Callable[[str, str], object] | None = None,
    ) -> None:
        self._base_url = base_url or os.getenv("JIRA_BASE_URL")
        if not self._base_url and client_factory is None:
            raise ValueError("JIRA_BASE_URL is required for JiraStatusPoller.")
        self._client_factory = client_factory

    def poll(self, *, provider: str, external_id: str, config: dict) -> ExternalTaskStatus:
        api_token = config.get("apiToken", os.getenv("JIRA_API_TOKEN", ""))
        user_email = config.get("userEmail", os.getenv("JIRA_USER_EMAIL", ""))

        response = self._build_session(api_token, user_email).get(
            f"{self._base_url}/rest/api/3/issue/{external_id}",
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        status = data["fields"]["status"]["name"]
        return ExternalTaskStatus(external_id=external_id, status=status, provider="jira")

    def _build_session(self, api_token: str, user_email: str):
        if self._client_factory is not None:
            return self._client_factory(api_token, user_email)
        import requests
        from requests.auth import HTTPBasicAuth
        session = requests.Session()
        session.auth = HTTPBasicAuth(user_email, api_token)
        return session


class GitHubStatusPoller:
    """Fetches the current state of a GitHub Issue via the REST API."""

    def __init__(
        self,
        base_url: str | None = None,
        client_factory: Callable[[str], object] | None = None,
    ) -> None:
        self._base_url = (base_url or os.getenv("GITHUB_API_URL", "https://api.github.com")).rstrip("/")
        self._client_factory = client_factory

    def poll(self, *, provider: str, external_id: str, config: dict) -> ExternalTaskStatus:
        token = config.get("token", os.getenv("GITHUB_TOKEN", ""))
        owner = config.get("owner", "")
        repo = config.get("repo", "")

        response = self._build_session(token).get(
            f"{self._base_url}/repos/{owner}/{repo}/issues/{external_id}",
            headers={"Accept": "application/vnd.github+json"},
        )
        response.raise_for_status()
        data = response.json()
        state = data["state"].upper()
        return ExternalTaskStatus(external_id=external_id, status=state, provider="github")

    def _build_session(self, token: str):
        if self._client_factory is not None:
            return self._client_factory(token)
        import requests
        session = requests.Session()
        session.headers["Authorization"] = f"Bearer {token}"
        return session


def build_poller(provider: str, config: dict | None = None):
    """Factory that returns the right poller for a given provider name."""
    if provider == "jira":
        return JiraStatusPoller()
    if provider == "github":
        return GitHubStatusPoller()
    raise ValueError(f"Unsupported provider for status polling: {provider!r}")
