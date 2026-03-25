from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RawDocument(BaseModel):
    """Raw document fetched from a connector before parsing."""

    source_type: str
    source_id: str
    title: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class Document(BaseModel):
    """Parsed and cleaned document ready for chunking."""

    id: str
    source_type: str
    source_id: str
    title: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class Chunk(BaseModel):
    """A chunk of a document with optional embedding."""

    id: str
    document_id: str
    content: str
    index: int
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] | None = None
