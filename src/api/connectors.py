import structlog
from fastapi import APIRouter, Depends, HTTPException

from src.connectors.base import BaseConnector
from src.dependencies import get_connectors, get_metadata_store
from src.models.connector import ConnectorState, ConnectorType, SyncStatus
from src.store.metadata import MetadataStore

logger = structlog.get_logger()

router = APIRouter()


@router.get("/connectors", response_model=list[ConnectorState])
async def list_connectors(
    metadata_store: MetadataStore = Depends(get_metadata_store),
) -> list[ConnectorState]:
    """List all connectors and their current state."""
    return await metadata_store.get_all_connector_states()


@router.post("/connectors/{connector_type}/sync")
async def sync_connector(
    connector_type: ConnectorType,
    connectors: dict[ConnectorType, BaseConnector] = Depends(get_connectors),
    metadata_store: MetadataStore = Depends(get_metadata_store),
) -> dict:
    """Trigger a sync for the given connector."""
    connector = connectors.get(connector_type)
    if not connector or not connector.is_configured():
        raise HTTPException(status_code=400, detail=f"Connector {connector_type} is not configured")

    await metadata_store.update_sync_state(connector_type, status=SyncStatus.RUNNING)

    try:
        state = await metadata_store.get_connector_state(connector_type)
        documents = await connector.fetch(since=state.last_sync_at)

        for doc in documents:
            await metadata_store.upsert_document(
                doc_id=f"{doc.source_type}:{doc.source_id}",
                source_type=doc.source_type,
                source_id=doc.source_id,
                title=doc.title,
                timestamp=doc.timestamp,
            )

        await metadata_store.update_sync_state(
            connector_type,
            status=SyncStatus.SUCCESS,
            document_count=len(documents),
        )

        logger.info("sync_completed", connector=connector_type, documents=len(documents))
        return {
            "status": "success",
            "connector": connector_type,
            "documents_fetched": len(documents),
        }

    except Exception as e:
        logger.error("sync_failed", connector=connector_type, error=str(e))
        await metadata_store.update_sync_state(
            connector_type, status=SyncStatus.FAILED, error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Sync failed: {e}") from e


@router.get("/connectors/{connector_type}/status", response_model=ConnectorState)
async def connector_status(
    connector_type: ConnectorType,
    metadata_store: MetadataStore = Depends(get_metadata_store),
) -> ConnectorState:
    """Get current status of a connector."""
    return await metadata_store.get_connector_state(connector_type)
