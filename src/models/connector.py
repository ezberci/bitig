from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class ConnectorType(StrEnum):
    GMAIL = "gmail"
    JIRA = "jira"
    MEET = "meet"


class SyncStatus(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class ConnectorState(BaseModel):
    """Current state of a connector."""

    connector_type: ConnectorType
    configured: bool = False
    status: SyncStatus = SyncStatus.IDLE
    last_sync_at: datetime | None = None
    document_count: int = 0
    error: str | None = None


class IngestionStats(BaseModel):
    """Overall ingestion statistics."""

    total_documents: int = 0
    total_chunks: int = 0
    total_entities: int = 0
    total_relations: int = 0
