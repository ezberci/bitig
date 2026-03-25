import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.llm.claude import ClaudeLLM


@pytest.fixture
def claude_llm():
    return ClaudeLLM(api_key="test-key", model="claude-sonnet-4-20250514")


def _mock_message(text: str) -> MagicMock:
    block = MagicMock()
    block.text = text
    msg = MagicMock()
    msg.content = [block]
    return msg


class TestClaudeGenerate:
    async def test_generate_basic(self, claude_llm):
        with patch.object(
            claude_llm._client.messages, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = _mock_message("Hello world")
            result = await claude_llm.generate("Say hello")

        assert result == "Hello world"
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["model"] == "claude-sonnet-4-20250514"
        assert call_kwargs["messages"][0]["content"] == "Say hello"
        assert "system" not in call_kwargs

    async def test_generate_with_system(self, claude_llm):
        with patch.object(
            claude_llm._client.messages, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = _mock_message("Hi")
            await claude_llm.generate("Hello", system="Be brief")

        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["system"] == "Be brief"


class TestClaudeGenerateStructured:
    async def test_generate_structured(self, claude_llm):
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        expected = {"name": "test"}

        with patch.object(
            claude_llm._client.messages, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = _mock_message(json.dumps(expected))
            result = await claude_llm.generate_structured("Extract name", schema)

        assert result == expected


class TestClaudeFactory:
    def test_create_claude_from_settings(self):
        from src.config import Settings
        from src.llm import create_llm

        settings = Settings(llm_provider="claude", claude_api_key="sk-test")
        llm = create_llm(settings)
        assert isinstance(llm, ClaudeLLM)

    def test_create_claude_without_key_raises(self):
        from src.config import Settings
        from src.llm import create_llm

        settings = Settings(llm_provider="claude", claude_api_key=None)
        with pytest.raises(ValueError, match="claude_api_key is required"):
            create_llm(settings)
