import hashlib
import re
from datetime import datetime

import structlog

from src.llm.base import BaseLLM
from src.models.entity import Entity, EntityType, Relation, RelationType

logger = structlog.get_logger()

# Rule-based patterns
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
TICKET_PATTERN = re.compile(r"\b[A-Z]{2,10}-\d{1,6}\b")

ENTITY_EXTRACTION_PROMPT = """\
Extract entities from the following text. Return JSON with this structure:
{{
  "entities": [
    {{"name": "...", "type": "person|project|topic|decision|action_item"}}
  ]
}}

Only extract clearly identifiable entities. Do not guess or hallucinate.
Types:
- person: Named individuals
- project: Project or product names
- topic: Technical topics, technologies, concepts
- decision: Specific decisions made
- action_item: Tasks or action items assigned

Text:
{text}
"""

ENTITY_SCHEMA = {
    "type": "object",
    "properties": {
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                },
                "required": ["name", "type"],
            },
        }
    },
    "required": ["entities"],
}


def _entity_id(name: str, entity_type: str) -> str:
    """Generate a stable entity ID from name and type."""
    key = f"{entity_type}:{name.lower().strip()}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def extract_rule_based(text: str) -> list[Entity]:
    """Extract entities using regex patterns."""
    now = datetime.now()
    entities: list[Entity] = []

    for match in EMAIL_PATTERN.finditer(text):
        email = match.group()
        name = email.split("@")[0].replace(".", " ").title()
        entities.append(
            Entity(
                id=_entity_id(email, "person"),
                name=name,
                type=EntityType.PERSON,
                metadata={"email": email},
                first_seen=now,
                last_seen=now,
            )
        )

    for match in TICKET_PATTERN.finditer(text):
        ticket = match.group()
        entities.append(
            Entity(
                id=_entity_id(ticket, "ticket"),
                name=ticket,
                type=EntityType.TICKET,
                metadata={},
                first_seen=now,
                last_seen=now,
            )
        )

    return entities


async def extract_llm_based(text: str, llm: BaseLLM) -> list[Entity]:
    """Extract entities using LLM."""
    now = datetime.now()
    prompt = ENTITY_EXTRACTION_PROMPT.format(text=text[:3000])

    try:
        result = await llm.generate_structured(
            prompt,
            ENTITY_SCHEMA,
            system="You are an entity extraction assistant. Be precise and concise.",
        )
    except Exception:
        logger.warning("llm_entity_extraction_failed", exc_info=True)
        return []

    entities: list[Entity] = []
    valid_types = {t.value for t in EntityType}

    for item in result.get("entities", []):
        name = item.get("name", "").strip()
        etype = item.get("type", "").lower().strip()
        if not name or etype not in valid_types:
            continue
        entities.append(
            Entity(
                id=_entity_id(name, etype),
                name=name,
                type=EntityType(etype),
                metadata={"source": "llm"},
                first_seen=now,
                last_seen=now,
            )
        )

    return entities


async def extract_entities(text: str, llm: BaseLLM | None = None) -> list[Entity]:
    """Hybrid entity extraction: rule-based + optional LLM.

    Args:
        text: The text to extract entities from.
        llm: Optional LLM for deeper extraction.

    Returns:
        Deduplicated list of entities.
    """
    entities = extract_rule_based(text)

    if llm:
        llm_entities = await extract_llm_based(text, llm)
        # Merge by ID (rule-based takes precedence)
        seen_ids = {e.id for e in entities}
        for e in llm_entities:
            if e.id not in seen_ids:
                entities.append(e)
                seen_ids.add(e.id)

    return entities


def build_relations(entities: list[Entity], document_id: str) -> list[Relation]:
    """Build MENTIONED_IN relations between entities and a document.

    Args:
        entities: Entities found in the document.
        document_id: The document they were found in.

    Returns:
        List of relations.
    """
    relations: list[Relation] = []
    for entity in entities:
        relations.append(
            Relation(
                entity_a_id=entity.id,
                entity_b_id=document_id,
                relation_type=RelationType.MENTIONED_IN,
                document_id=document_id,
            )
        )
    return relations
