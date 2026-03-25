import base64
from pathlib import Path

import pytest

from src.connectors.gmail import GmailConnector


@pytest.fixture
def gmail_connector():
    return GmailConnector(credentials_path=None)


class TestGmailConnector:
    def test_connector_type(self, gmail_connector):
        assert gmail_connector.connector_type == "gmail"

    def test_not_configured_without_path(self, gmail_connector):
        assert gmail_connector.is_configured() is False

    def test_not_configured_with_nonexistent_path(self):
        connector = GmailConnector(credentials_path=Path("/nonexistent/creds.json"))
        assert connector.is_configured() is False

    async def test_fetch_returns_empty_when_not_configured(self, gmail_connector):
        docs = await gmail_connector.fetch()
        assert docs == []


class TestGmailParseMessage:
    def test_parse_plain_message(self, gmail_connector):
        body_data = base64.urlsafe_b64encode(b"Hello, this is a test email").decode()
        msg = {
            "id": "msg123",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "alice@example.com"},
                    {"name": "To", "value": "bob@example.com"},
                    {"name": "Date", "value": "Mon, 15 Jan 2024 10:00:00 +0000"},
                ],
                "body": {"data": body_data},
                "parts": [],
            },
        }

        doc = gmail_connector._parse_message(msg)
        assert doc is not None
        assert doc.source_type == "gmail"
        assert doc.source_id == "msg123"
        assert doc.title == "Test Subject"
        assert "Hello" in doc.content
        assert doc.metadata["from"] == "alice@example.com"

    def test_parse_multipart_message(self, gmail_connector):
        body_data = base64.urlsafe_b64encode(b"Plain text body").decode()
        msg = {
            "id": "msg456",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Multipart"},
                    {"name": "From", "value": "alice@example.com"},
                    {"name": "Date", "value": "Tue, 16 Jan 2024 10:00:00 +0000"},
                ],
                "body": {},
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": body_data},
                    },
                    {
                        "mimeType": "text/html",
                        "body": {"data": base64.urlsafe_b64encode(b"<p>HTML</p>").decode()},
                    },
                ],
            },
        }

        doc = gmail_connector._parse_message(msg)
        assert doc is not None
        assert "Plain text body" in doc.content

    def test_parse_message_no_body_returns_none(self, gmail_connector):
        msg = {
            "id": "msg789",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Empty"},
                    {"name": "From", "value": "alice@example.com"},
                    {"name": "Date", "value": "Wed, 17 Jan 2024 10:00:00 +0000"},
                ],
                "body": {},
                "parts": [],
            },
        }

        doc = gmail_connector._parse_message(msg)
        assert doc is None
