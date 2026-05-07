from connectors.issues import GitHubIssuesConnector, JiraConnector


def test_jira_connector_returns_jira_specific_metadata():
    result = JiraConnector().create_issue(provider="jira", title="Fix login timeout", description="Investigate")
    assert result.provider == "jira"
    assert result.external_id == "JIRA-101"
    assert result.external_url.startswith("https://jira.example.com/browse/")


def test_github_connector_returns_github_specific_metadata():
    result = GitHubIssuesConnector().create_issue(provider="github", title="Fix login timeout", description="Investigate")
    assert result.provider == "github"
    assert result.external_id == "GH-101"
    assert result.external_url.startswith("https://github.com/")

