from unittest.mock import AsyncMock

import pytest

from src.rag.pipeline import RAGPipeline


@pytest.fixture
def mock_retriever():
    retriever = AsyncMock()
    retriever.retrieve.return_value = [
        {
            "id": "chunk-1",
            "score": 0.95,
            "content": "Meeting notes from standup",
            "metadata": {
                "document_id": "doc-1",
                "source_type": "meet",
                "title": "Standup",
                "timestamp": "2024-01-15T10:00:00",
            },
        }
    ]
    return retriever


@pytest.fixture
def mock_generator():
    generator = AsyncMock()
    generator.generate.return_value = "The standup covered sprint goals."
    return generator


@pytest.fixture
def mock_metadata():
    return AsyncMock()


@pytest.fixture
def pipeline(mock_retriever, mock_generator, mock_metadata):
    return RAGPipeline(
        retriever=mock_retriever,
        generator=mock_generator,
        metadata_store=mock_metadata,
    )


class TestRAGPipeline:
    async def test_ask_returns_response(self, pipeline):
        response = await pipeline.ask("What was discussed?")
        assert response.answer == "The standup covered sprint goals."
        assert len(response.sources) == 1
        assert response.sources[0].source_type == "meet"

    async def test_ask_saves_to_history(self, pipeline, mock_metadata):
        await pipeline.ask("test question")
        mock_metadata.save_chat.assert_called_once()
        saved = mock_metadata.save_chat.call_args[0][0]
        assert saved.question == "test question"

    async def test_ask_passes_filters(self, pipeline, mock_retriever):
        await pipeline.ask("test", top_k=10, source_filter="gmail")
        call_kwargs = mock_retriever.retrieve.call_args.kwargs
        assert call_kwargs["top_k"] == 10
        assert call_kwargs["source_filter"] == "gmail"

    async def test_ask_no_results(self, pipeline, mock_retriever, mock_generator):
        mock_retriever.retrieve.return_value = []
        mock_generator.generate.return_value = "No info found."

        response = await pipeline.ask("unknown topic")
        assert response.sources == []
