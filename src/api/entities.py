from fastapi import APIRouter, Depends, Query

from src.dependencies import get_metadata_store
from src.models.entity import Entity, EntityGraph, EntityType
from src.store.metadata import MetadataStore

router = APIRouter()


@router.get("/entities", response_model=list[Entity])
async def list_entities(
    entity_type: EntityType | None = None,
    q: str | None = Query(None, description="Search query for entity name"),
    limit: int = 50,
    metadata_store: MetadataStore = Depends(get_metadata_store),
) -> list[Entity]:
    """List entities with optional filtering."""
    return await metadata_store.get_entities(entity_type=entity_type, query=q, limit=limit)


@router.get("/entities/graph", response_model=EntityGraph)
async def entity_graph(
    metadata_store: MetadataStore = Depends(get_metadata_store),
) -> EntityGraph:
    """Get entity graph data for visualization."""
    return await metadata_store.get_entity_graph()


@router.get("/entities/{entity_id}", response_model=Entity)
async def get_entity(
    entity_id: str,
    metadata_store: MetadataStore = Depends(get_metadata_store),
) -> Entity:
    """Get a single entity with its relations."""
    return await metadata_store.get_entity(entity_id)
