import structlog

from src.ingestion.embedder import Embedder
from src.store.qdrant import QdrantStore

logger = structlog.get_logger()


class Retriever:
    """Embeds a query and searches Qdrant for relevant chunks."""

    def __init__(self, embedder: Embedder, qdrant_store: QdrantStore) -> None:
        self._embedder = embedder
        self._qdrant = qdrant_store

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        source_filter: str | None = None,
    ) -> list[dict]:
        """Retrieve relevant chunks for a query.

        Args:
            query: Natural language query.
            top_k: Number of results to return.
            source_filter: Optional source type filter.

        Returns:
            List of search result dicts with content and metadata.
        """
        query_vector = self._embedder.embed_query(query)
        results = await self._qdrant.search(
            query_vector=query_vector,
            top_k=top_k,
            source_filter=source_filter,
        )
        logger.info("retriever_results", query=query[:50], count=len(results))
        return results
