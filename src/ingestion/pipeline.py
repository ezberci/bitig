import structlog
from qdrant_client.models import PointStruct

from src.ingestion.chunker import chunk_document, raw_to_document
from src.ingestion.embedder import Embedder
from src.models.document import RawDocument
from src.store.metadata import MetadataStore
from src.store.qdrant import QdrantStore

logger = structlog.get_logger()


class IngestionPipeline:
    """Orchestrates: raw docs → parse → chunk → embed → store."""

    def __init__(
        self,
        metadata_store: MetadataStore,
        qdrant_store: QdrantStore,
        embedder: Embedder,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ) -> None:
        self._metadata = metadata_store
        self._qdrant = qdrant_store
        self._embedder = embedder
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    async def ingest(self, raw_docs: list[RawDocument]) -> int:
        """Ingest a batch of raw documents.

        Args:
            raw_docs: List of raw documents from a connector.

        Returns:
            Total number of chunks stored.
        """
        if not raw_docs:
            return 0

        total_chunks = 0

        for raw in raw_docs:
            doc = raw_to_document(raw)

            chunks = chunk_document(
                doc,
                chunk_size=self._chunk_size,
                chunk_overlap=self._chunk_overlap,
            )
            if not chunks:
                continue

            self._embedder.embed_chunks(chunks)

            points = [
                PointStruct(
                    id=chunk.id,
                    vector=chunk.embedding,
                    payload={
                        "content": chunk.content,
                        "document_id": chunk.document_id,
                        "chunk_index": chunk.index,
                        **chunk.metadata,
                    },
                )
                for chunk in chunks
                if chunk.embedding is not None
            ]

            await self._qdrant.upsert_chunks(points)

            await self._metadata.upsert_document(
                doc_id=doc.id,
                source_type=doc.source_type,
                source_id=doc.source_id,
                title=doc.title,
                timestamp=doc.timestamp,
            )

            total_chunks += len(points)
            logger.info(
                "document_ingested",
                doc_id=doc.id,
                title=doc.title,
                chunks=len(points),
            )

        logger.info("ingestion_complete", documents=len(raw_docs), chunks=total_chunks)
        return total_chunks
