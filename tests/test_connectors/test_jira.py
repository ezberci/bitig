import pytest

from src.connectors.jira import JiraConnector


@pytest.fixture
def jira_connector():
    return JiraConnector(
        url="https://test.atlassian.net",
        email="test@example.com",
        api_token="test-token",
    )


@pytest.fixture
def unconfigured_jira():
    return JiraConnector()


class TestJiraConnector:
    def test_connector_type(self, jira_connector):
        assert jira_connector.connector_type == "jira"

    def test_is_configured(self, jira_connector):
        assert jira_connector.is_configured() is True

    def test_not_configured(self, unconfigured_jira):
        assert unconfigured_jira.is_configured() is False

    async def test_fetch_returns_empty_when_not_configured(self, unconfigured_jira):
        docs = await unconfigured_jira.fetch()
        assert docs == []


class TestJiraParseIssue:
    def test_parse_basic_issue(self, jira_connector):
        issue = {
            "key": "PROJ-123",
            "fields": {
                "summary": "Fix login bug",
                "description": {"content": [{"type": "text", "text": "Users cannot login"}]},
                "status": {"name": "In Progress"},
                "assignee": {"displayName": "Alice"},
                "priority": {"name": "High"},
                "updated": "2024-01-15T10:00:00.000+0000",
                "created": "2024-01-10T08:00:00.000+0000",
            },
        }

        doc = jira_connector._parse_issue(issue)
        assert doc.source_type == "jira"
        assert doc.source_id == "PROJ-123"
        assert "[PROJ-123]" in doc.title
        assert "Fix login bug" in doc.title
        assert "Users cannot login" in doc.content
        assert doc.metadata["status"] == "In Progress"
        assert doc.metadata["assignee"] == "Alice"

    def test_parse_issue_with_comments(self, jira_connector):
        issue = {
            "key": "PROJ-456",
            "fields": {
                "summary": "Add feature",
                "description": None,
                "comment": {
                    "comments": [
                        {
                            "author": {"displayName": "Bob"},
                            "body": {"content": [{"type": "text", "text": "Working on it"}]},
                        }
                    ]
                },
                "status": {"name": "Open"},
                "assignee": None,
                "priority": None,
                "updated": "2024-01-15T10:00:00.000+0000",
            },
        }

        doc = jira_connector._parse_issue(issue)
        assert "[Bob]" in doc.content
        assert "Working on it" in doc.content

    def test_parse_issue_no_description(self, jira_connector):
        issue = {
            "key": "PROJ-789",
            "fields": {
                "summary": "Empty issue",
                "description": None,
                "status": {"name": "Done"},
                "assignee": None,
                "priority": None,
                "created": "2024-01-15T10:00:00.000+0000",
            },
        }

        doc = jira_connector._parse_issue(issue)
        assert doc.source_id == "PROJ-789"


class TestJiraExtractText:
    def test_extract_simple_text(self, jira_connector):
        adf = {"content": [{"type": "text", "text": "Hello world"}]}
        assert jira_connector._extract_text(adf) == "Hello world"

    def test_extract_nested_text(self, jira_connector):
        adf = {
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Nested text"}],
                }
            ]
        }
        assert "Nested text" in jira_connector._extract_text(adf)

    def test_extract_from_string(self, jira_connector):
        assert jira_connector._extract_text("plain string") == "plain string"

    def test_extract_from_none(self, jira_connector):
        assert jira_connector._extract_text(None) == ""
