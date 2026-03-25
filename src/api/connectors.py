from fastapi import APIRouter, Depends

from src.dependencies import get_metadata_store
from src.models.connector import ConnectorState, ConnectorType
from src.store.metadata import MetadataStore

router = APIRouter()


@router.get("/connectors", response_model=list[ConnectorState])
async def list_connectors(
    metadata_store: MetadataStore = Depends(get_metadata_store),
) -> list[ConnectorState]:
    """List all connectors and their current state."""
    return await metadata_store.get_all_connector_states()


@router.post("/connectors/{connector_type}/sync")
async def sync_connector(connector_type: ConnectorType) -> dict:
    """Trigger a sync for the given connector."""
    # TODO: Implement ingestion pipeline in Phase 2
    return {"status": "not_implemented", "connector": connector_type}


@router.get("/connectors/{connector_type}/status", response_model=ConnectorState)
async def connector_status(
    connector_type: ConnectorType,
    metadata_store: MetadataStore = Depends(get_metadata_store),
) -> ConnectorState:
    """Get current status of a connector."""
    return await metadata_store.get_connector_state(connector_type)
