from fastapi import APIRouter, Depends

from src.dependencies import get_metadata_store
from src.models.connector import IngestionStats
from src.store.metadata import MetadataStore

router = APIRouter()


@router.get("/ingestion/stats", response_model=IngestionStats)
async def ingestion_stats(
    metadata_store: MetadataStore = Depends(get_metadata_store),
) -> IngestionStats:
    """Get overall ingestion statistics."""
    return await metadata_store.get_ingestion_stats()
