from unittest.mock import AsyncMock, MagicMock

import pytest

from src.rag.retriever import Retriever


@pytest.fixture
def mock_embedder():
    embedder = MagicMock()
    embedder.embed_query.return_value = [0.1] * 384
    return embedder


@pytest.fixture
def mock_qdrant():
    return AsyncMock()


@pytest.fixture
def retriever(mock_embedder, mock_qdrant):
    return Retriever(embedder=mock_embedder, qdrant_store=mock_qdrant)


class TestRetriever:
    async def test_retrieve_embeds_and_searches(self, retriever, mock_embedder, mock_qdrant):
        mock_qdrant.search.return_value = [
            {"id": "1", "score": 0.9, "content": "result", "metadata": {}}
        ]

        results = await retriever.retrieve("test query")

        mock_embedder.embed_query.assert_called_once_with("test query")
        mock_qdrant.search.assert_called_once()
        assert len(results) == 1

    async def test_retrieve_passes_top_k(self, retriever, mock_qdrant):
        mock_qdrant.search.return_value = []
        await retriever.retrieve("test", top_k=10)

        call_kwargs = mock_qdrant.search.call_args.kwargs
        assert call_kwargs["top_k"] == 10

    async def test_retrieve_passes_source_filter(self, retriever, mock_qdrant):
        mock_qdrant.search.return_value = []
        await retriever.retrieve("test", source_filter="gmail")

        call_kwargs = mock_qdrant.search.call_args.kwargs
        assert call_kwargs["source_filter"] == "gmail"
