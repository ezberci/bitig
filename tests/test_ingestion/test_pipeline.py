from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.ingestion.pipeline import IngestionPipeline
from src.models.document import RawDocument


@pytest.fixture
def mock_metadata():
    store = AsyncMock()
    return store


@pytest.fixture
def mock_qdrant():
    store = AsyncMock()
    return store


@pytest.fixture
def mock_embedder():
    embedder = MagicMock()
    embedder.embed_chunks.side_effect = lambda chunks: [
        setattr(c, "embedding", [0.1] * 384) or c for c in chunks
    ]
    return embedder


@pytest.fixture
def pipeline(mock_metadata, mock_qdrant, mock_embedder):
    return IngestionPipeline(
        metadata_store=mock_metadata,
        qdrant_store=mock_qdrant,
        embedder=mock_embedder,
        chunk_size=512,
        chunk_overlap=64,
    )


def _make_raw_doc(source_id: str = "doc1", content: str = "Test content") -> RawDocument:
    return RawDocument(
        source_type="test",
        source_id=source_id,
        title="Test Doc",
        content=content,
        timestamp=datetime(2024, 1, 15),
    )


class TestIngestionPipeline:
    async def test_ingest_empty_list(self, pipeline):
        result = await pipeline.ingest([])
        assert result == 0

    async def test_ingest_single_doc(self, pipeline, mock_qdrant, mock_metadata):
        raw = _make_raw_doc(content="Hello world, this is a test document.")
        result = await pipeline.ingest([raw])

        assert result > 0
        mock_qdrant.upsert_chunks.assert_called_once()
        mock_metadata.upsert_document.assert_called_once()

    async def test_ingest_multiple_docs(self, pipeline, mock_qdrant, mock_metadata):
        docs = [_make_raw_doc(source_id=f"doc{i}", content=f"Content {i}") for i in range(3)]
        result = await pipeline.ingest(docs)

        assert result > 0
        assert mock_qdrant.upsert_chunks.call_count == 3
        assert mock_metadata.upsert_document.call_count == 3

    async def test_ingest_empty_content_skipped(self, pipeline, mock_qdrant):
        raw = _make_raw_doc(content="")
        result = await pipeline.ingest([raw])

        assert result == 0
        mock_qdrant.upsert_chunks.assert_not_called()

    async def test_points_have_correct_payload(self, pipeline, mock_qdrant):
        raw = _make_raw_doc(content="Important meeting notes about the project")
        await pipeline.ingest([raw])

        points = mock_qdrant.upsert_chunks.call_args[0][0]
        assert len(points) > 0
        point = points[0]
        assert "content" in point.payload
        assert "document_id" in point.payload
        assert "source_type" in point.payload
        assert point.payload["source_type"] == "test"
