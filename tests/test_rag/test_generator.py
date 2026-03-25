from unittest.mock import AsyncMock

import pytest

from src.rag.generator import Generator


@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.generate.return_value = "The answer is 42."
    return llm


@pytest.fixture
def generator(mock_llm):
    return Generator(llm=mock_llm)


class TestGenerator:
    async def test_generate_with_context(self, generator, mock_llm):
        chunks = [
            {
                "content": "Important info here",
                "metadata": {"source_type": "gmail", "title": "Email 1"},
            }
        ]

        result = await generator.generate("What is important?", chunks)

        assert result == "The answer is 42."
        mock_llm.generate.assert_called_once()
        call_args = mock_llm.generate.call_args
        assert "Important info here" in call_args.args[0]
        assert "What is important?" in call_args.args[0]

    async def test_generate_empty_context(self, generator, mock_llm):
        result = await generator.generate("test?", [])
        assert "couldn't find" in result.lower()
        mock_llm.generate.assert_not_called()

    async def test_format_context_multiple_chunks(self, generator):
        chunks = [
            {"content": "First", "metadata": {"source_type": "gmail", "title": "A"}},
            {"content": "Second", "metadata": {"source_type": "jira", "title": "B"}},
        ]
        ctx = generator._format_context(chunks)
        assert "[Source 1:" in ctx
        assert "[Source 2:" in ctx
        assert "First" in ctx
        assert "Second" in ctx
