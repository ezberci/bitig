from fastapi import APIRouter, Depends

from src.dependencies import get_metadata_store, get_qdrant_store
from src.models.connector import IngestionStats
from src.store.metadata import MetadataStore
from src.store.qdrant import QdrantStore

router = APIRouter()


@router.get("/ingestion/stats", response_model=IngestionStats)
async def ingestion_stats(
    metadata_store: MetadataStore = Depends(get_metadata_store),
    qdrant_store: QdrantStore = Depends(get_qdrant_store),
) -> IngestionStats:
    """Get overall ingestion statistics."""
    stats = await metadata_store.get_ingestion_stats()
    stats.total_chunks = await qdrant_store.get_collection_count()
    return stats
