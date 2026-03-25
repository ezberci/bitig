from datetime import datetime

from pydantic import BaseModel, Field


class Source(BaseModel):
    """A source reference included in a chat response."""

    document_id: str
    title: str
    source_type: str
    snippet: str
    timestamp: datetime


class ChatRequest(BaseModel):
    """Incoming chat request."""

    question: str
    top_k: int = 5
    source_filter: str | None = None


class ChatResponse(BaseModel):
    """Chat response with answer and sources."""

    answer: str
    sources: list[Source] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class ChatHistoryItem(BaseModel):
    """A single chat exchange in history."""

    id: str
    question: str
    answer: str
    sources: list[Source] = Field(default_factory=list)
    created_at: datetime
