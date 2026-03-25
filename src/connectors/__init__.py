from src.config import Settings
from src.connectors.base import BaseConnector
from src.connectors.gmail import GmailConnector
from src.connectors.jira import JiraConnector
from src.connectors.meet import MeetConnector
from src.models.connector import ConnectorType


def create_connectors(settings: Settings) -> dict[ConnectorType, BaseConnector]:
    """Create all connector instances from settings.

    Returns:
        Mapping of connector type to connector instance.
    """
    return {
        ConnectorType.GMAIL: GmailConnector(
            credentials_path=settings.gmail_credentials_path,
        ),
        ConnectorType.JIRA: JiraConnector(
            url=settings.jira_url,
            email=settings.jira_email,
            api_token=settings.jira_api_token,
        ),
        ConnectorType.MEET: MeetConnector(),
    }


__all__ = [
    "BaseConnector",
    "GmailConnector",
    "JiraConnector",
    "MeetConnector",
    "create_connectors",
]
