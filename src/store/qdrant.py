import structlog
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.config import settings

logger = structlog.get_logger()


class QdrantStore:
    """Async wrapper around Qdrant vector database."""

    def __init__(self) -> None:
        self.client = AsyncQdrantClient(url=settings.qdrant_url)
        self.collection = settings.qdrant_collection

    async def initialize(self) -> None:
        """Create collection if it doesn't exist."""
        collections = await self.client.get_collections()
        existing = [c.name for c in collections.collections]

        if self.collection not in existing:
            await self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            logger.info("qdrant_collection_created", collection=self.collection)
        else:
            logger.info("qdrant_collection_exists", collection=self.collection)

    async def upsert_chunks(self, points: list[PointStruct]) -> None:
        """Upsert chunk vectors into Qdrant."""
        if not points:
            return
        await self.client.upsert(collection_name=self.collection, points=points)
        logger.info("qdrant_upserted", count=len(points))

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        source_filter: str | None = None,
    ) -> list[dict]:
        """Search for similar chunks."""
        query_filter = None
        if source_filter:
            from qdrant_client.models import FieldCondition, Filter, MatchValue

            query_filter = Filter(
                must=[FieldCondition(key="source_type", match=MatchValue(value=source_filter))]
            )

        results = await self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter,
        )

        return [
            {
                "id": str(hit.id),
                "score": hit.score,
                "content": hit.payload.get("content", "") if hit.payload else "",
                "metadata": hit.payload or {},
            }
            for hit in results
        ]

    async def get_collection_count(self) -> int:
        """Get total number of points in collection."""
        try:
            info = await self.client.get_collection(self.collection)
            return info.points_count or 0
        except Exception:
            return 0
