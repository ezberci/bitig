import base64
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

import structlog
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from src.connectors.base import BaseConnector
from src.models.connector import ConnectorType
from src.models.document import RawDocument

logger = structlog.get_logger()


class GmailConnector(BaseConnector):
    """Connector for fetching emails from Gmail via Google API."""

    def __init__(self, credentials_path: Path | None = None) -> None:
        self._credentials_path = credentials_path
        self._service = None

    @property
    def connector_type(self) -> ConnectorType:
        return ConnectorType.GMAIL

    def is_configured(self) -> bool:
        return self._credentials_path is not None and self._credentials_path.exists()

    def _get_service(self):
        if self._service is None:
            creds = Credentials.from_authorized_user_file(str(self._credentials_path))
            self._service = build("gmail", "v1", credentials=creds)
        return self._service

    async def fetch(self, since: datetime | None = None) -> list[RawDocument]:
        if not self.is_configured():
            logger.warning("gmail_not_configured")
            return []

        service = self._get_service()
        query = ""
        if since:
            query = f"after:{since.strftime('%Y/%m/%d')}"

        results = service.users().messages().list(userId="me", q=query, maxResults=100).execute()

        messages = results.get("messages", [])
        documents: list[RawDocument] = []

        for msg_ref in messages:
            msg = (
                service.users()
                .messages()
                .get(userId="me", id=msg_ref["id"], format="full")
                .execute()
            )
            doc = self._parse_message(msg)
            if doc:
                documents.append(doc)

        logger.info("gmail_fetched", count=len(documents))
        return documents

    def _parse_message(self, msg: dict) -> RawDocument | None:
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        subject = headers.get("Subject", "(no subject)")
        sender = headers.get("From", "")
        date_str = headers.get("Date", "")

        try:
            timestamp = parsedate_to_datetime(date_str)
        except (ValueError, TypeError):
            timestamp = datetime.now()

        body = self._extract_body(msg["payload"])
        if not body:
            return None

        return RawDocument(
            source_type="gmail",
            source_id=msg["id"],
            title=subject,
            content=body,
            metadata={"from": sender, "to": headers.get("To", "")},
            timestamp=timestamp,
        )

    def _extract_body(self, payload: dict) -> str:
        if payload.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode(
                "utf-8", errors="replace"
            )

        for part in payload.get("parts", []):
            if part["mimeType"] == "text/plain" and part.get("body", {}).get("data"):
                return base64.urlsafe_b64decode(part["body"]["data"]).decode(
                    "utf-8", errors="replace"
                )

        for part in payload.get("parts", []):
            body = self._extract_body(part)
            if body:
                return body

        return ""
