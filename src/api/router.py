from fastapi import APIRouter, Depends

from src.api import chat, connectors, entities, health, ingestion
from src.api.middleware import verify_api_key

api_router = APIRouter(dependencies=[Depends(verify_api_key)])

api_router.include_router(health.router, tags=["health"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(connectors.router, tags=["connectors"])
api_router.include_router(entities.router, tags=["entities"])
api_router.include_router(ingestion.router, tags=["ingestion"])
