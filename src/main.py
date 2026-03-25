from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from src.api.router import api_router
from src.config import settings
from src.connectors import create_connectors
from src.ingestion.embedder import Embedder
from src.llm import create_llm
from src.rag.generator import Generator
from src.rag.pipeline import RAGPipeline
from src.rag.retriever import Retriever
from src.store.metadata import MetadataStore
from src.store.qdrant import QdrantStore

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize and cleanup application resources."""
    logger.info("starting_bitig")

    # Initialize stores
    metadata_store = MetadataStore()
    await metadata_store.initialize()
    app.state.metadata_store = metadata_store

    qdrant_store = QdrantStore()
    await qdrant_store.initialize()
    app.state.qdrant_store = qdrant_store

    # Initialize connectors
    app.state.connectors = create_connectors(settings)

    # Initialize RAG pipeline
    llm = create_llm(settings)
    embedder = Embedder(model_name=settings.embedding_model)
    retriever = Retriever(embedder=embedder, qdrant_store=qdrant_store)
    generator = Generator(llm=llm)
    app.state.rag_pipeline = RAGPipeline(
        retriever=retriever,
        generator=generator,
        metadata_store=metadata_store,
    )

    logger.info("bitig_ready")
    yield

    # Cleanup
    await metadata_store.close()
    logger.info("bitig_shutdown")


app = FastAPI(
    title="Bitig",
    description="Personal work memory platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router, prefix="/api")
