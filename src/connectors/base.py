from abc import ABC, abstractmethod
from datetime import datetime

from src.models.connector import ConnectorType
from src.models.document import RawDocument


class BaseConnector(ABC):
    """Abstract base class for data source connectors."""

    @property
    @abstractmethod
    def connector_type(self) -> ConnectorType:
        """The type identifier for this connector."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the connector has valid configuration."""

    @abstractmethod
    async def fetch(self, since: datetime | None = None) -> list[RawDocument]:
        """Fetch documents from the data source.

        Args:
            since: If provided, only fetch documents newer than this timestamp.

        Returns:
            List of raw documents fetched from the source.
        """
