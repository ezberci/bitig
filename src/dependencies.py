from fastapi import Request

from src.connectors.base import BaseConnector
from src.models.connector import ConnectorType
from src.rag.pipeline import RAGPipeline
from src.store.metadata import MetadataStore
from src.store.qdrant import QdrantStore


def get_metadata_store(request: Request) -> MetadataStore:
    return request.app.state.metadata_store


def get_qdrant_store(request: Request) -> QdrantStore:
    return request.app.state.qdrant_store


def get_connectors(request: Request) -> dict[ConnectorType, BaseConnector]:
    return request.app.state.connectors


def get_rag_pipeline(request: Request) -> RAGPipeline:
    return request.app.state.rag_pipeline
