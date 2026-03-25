from datetime import datetime

import httpx
import structlog

from src.connectors.base import BaseConnector
from src.models.connector import ConnectorType
from src.models.document import RawDocument

logger = structlog.get_logger()


class JiraConnector(BaseConnector):
    """Connector for fetching issues from Jira via REST API."""

    def __init__(
        self,
        url: str | None = None,
        email: str | None = None,
        api_token: str | None = None,
    ) -> None:
        self._url = url.rstrip("/") if url else None
        self._email = email
        self._api_token = api_token

    @property
    def connector_type(self) -> ConnectorType:
        return ConnectorType.JIRA

    def is_configured(self) -> bool:
        return all([self._url, self._email, self._api_token])

    async def fetch(self, since: datetime | None = None) -> list[RawDocument]:
        if not self.is_configured():
            logger.warning("jira_not_configured")
            return []

        jql = "ORDER BY updated DESC"
        if since:
            jql = f"updated >= '{since.strftime('%Y-%m-%d %H:%M')}' {jql}"

        documents: list[RawDocument] = []
        start_at = 0
        max_results = 50

        async with httpx.AsyncClient(
            base_url=self._url,
            auth=(self._email, self._api_token),
            timeout=30.0,
        ) as client:
            while True:
                response = await client.get(
                    "/rest/api/3/search",
                    params={"jql": jql, "startAt": start_at, "maxResults": max_results},
                )
                response.raise_for_status()
                data = response.json()

                for issue in data.get("issues", []):
                    doc = self._parse_issue(issue)
                    documents.append(doc)

                if start_at + max_results >= data.get("total", 0):
                    break
                start_at += max_results

        logger.info("jira_fetched", count=len(documents))
        return documents

    def _parse_issue(self, issue: dict) -> RawDocument:
        fields = issue["fields"]
        key = issue["key"]

        description = ""
        if fields.get("description"):
            description = self._extract_text(fields["description"])

        comments_text = ""
        comments = fields.get("comment", {}).get("comments", [])
        for comment in comments:
            author = comment.get("author", {}).get("displayName", "Unknown")
            body = self._extract_text(comment.get("body", {}))
            comments_text += f"\n[{author}]: {body}"

        content = f"{fields.get('summary', '')}\n\n{description}"
        if comments_text:
            content += f"\n\nComments:{comments_text}"

        timestamp_str = fields.get("updated") or fields.get("created", "")
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            timestamp = datetime.now()

        return RawDocument(
            source_type="jira",
            source_id=key,
            title=f"[{key}] {fields.get('summary', '')}",
            content=content,
            metadata={
                "key": key,
                "status": fields.get("status", {}).get("name", ""),
                "assignee": (fields.get("assignee") or {}).get("displayName", ""),
                "priority": (fields.get("priority") or {}).get("name", ""),
            },
            timestamp=timestamp,
        )

    def _extract_text(self, adf: dict) -> str:
        """Extract plain text from Atlassian Document Format (ADF)."""
        if isinstance(adf, str):
            return adf
        if not isinstance(adf, dict):
            return ""

        text_parts: list[str] = []
        for node in adf.get("content", []):
            if node.get("type") == "text":
                text_parts.append(node.get("text", ""))
            elif "content" in node:
                text_parts.append(self._extract_text(node))
        return " ".join(text_parts)
