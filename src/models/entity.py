from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class EntityType(StrEnum):
    PERSON = "person"
    PROJECT = "project"
    TICKET = "ticket"
    DECISION = "decision"
    ACTION_ITEM = "action_item"
    TOPIC = "topic"


class RelationType(StrEnum):
    MENTIONED_IN = "mentioned_in"
    DISCUSSED_IN = "discussed_in"
    DECIDED_IN = "decided_in"
    ASSIGNED_TO = "assigned_to"
    RELATED_TO = "related_to"


class Entity(BaseModel):
    """An extracted entity (person, ticket, decision, etc.)."""

    id: str
    name: str
    type: EntityType
    metadata: dict[str, str] = Field(default_factory=dict)
    first_seen: datetime
    last_seen: datetime


class Relation(BaseModel):
    """A relationship between two entities."""

    entity_a_id: str
    entity_b_id: str
    relation_type: RelationType
    document_id: str
    confidence: float = 1.0


class EntityGraph(BaseModel):
    """Graph data for frontend visualization."""

    nodes: list[Entity]
    edges: list[Relation]
