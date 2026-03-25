from fastapi import Request

from src.store.metadata import MetadataStore
from src.store.qdrant import QdrantStore


def get_metadata_store(request: Request) -> MetadataStore:
    return request.app.state.metadata_store


def get_qdrant_store(request: Request) -> QdrantStore:
    return request.app.state.qdrant_store
