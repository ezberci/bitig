import structlog
from thefuzz import fuzz

from src.models.entity import Entity

logger = structlog.get_logger()

DEFAULT_THRESHOLD = 85


def resolve_entities(
    new_entities: list[Entity],
    existing_entities: list[Entity],
    threshold: int = DEFAULT_THRESHOLD,
) -> list[Entity]:
    """Deduplicate entities by fuzzy matching names within the same type.

    If a new entity fuzzy-matches an existing one, the existing entity's
    last_seen is updated. Otherwise the new entity is kept as-is.

    Args:
        new_entities: Newly extracted entities.
        existing_entities: Previously stored entities.
        threshold: Fuzzy match score threshold (0-100).

    Returns:
        Resolved list of entities to upsert.
    """
    resolved: list[Entity] = []

    for new in new_entities:
        match = _find_match(new, existing_entities, threshold)
        if match:
            # Update existing entity's last_seen
            resolved.append(
                match.model_copy(
                    update={
                        "last_seen": new.last_seen,
                        "metadata": {**match.metadata, **new.metadata},
                    }
                )
            )
            logger.debug("entity_resolved", new=new.name, existing=match.name)
        else:
            resolved.append(new)

    return resolved


def _find_match(
    entity: Entity,
    candidates: list[Entity],
    threshold: int,
) -> Entity | None:
    """Find the best fuzzy match for an entity among candidates."""
    best_match: Entity | None = None
    best_score = 0

    for candidate in candidates:
        if candidate.type != entity.type:
            continue
        score = fuzz.ratio(entity.name.lower(), candidate.name.lower())
        if score >= threshold and score > best_score:
            best_match = candidate
            best_score = score

    return best_match
