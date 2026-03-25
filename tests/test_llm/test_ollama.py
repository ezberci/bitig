import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.llm.ollama import OllamaLLM


@pytest.fixture
def ollama_llm():
    return OllamaLLM(base_url="http://localhost:11434", model="llama3")


class TestOllamaGenerate:
    async def test_generate_basic(self, ollama_llm):
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "Hello world"}

        mock_post = AsyncMock(return_value=mock_response)
        with patch.object(ollama_llm._client, "post", mock_post):
            result = await ollama_llm.generate("Say hello")

        assert result == "Hello world"
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs["json"]
        assert payload["model"] == "llama3"
        assert payload["prompt"] == "Say hello"
        assert payload["stream"] is False
        assert "system" not in payload

    async def test_generate_with_system(self, ollama_llm):
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "Hi"}

        mock_post = AsyncMock(return_value=mock_response)
        with patch.object(ollama_llm._client, "post", mock_post):
            await ollama_llm.generate("Hello", system="Be brief")

        payload = mock_post.call_args.kwargs["json"]
        assert payload["system"] == "Be brief"


class TestOllamaGenerateStructured:
    async def test_generate_structured(self, ollama_llm):
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        expected = {"name": "test"}

        mock_response = MagicMock()
        mock_response.json.return_value = {"response": json.dumps(expected)}

        with patch.object(ollama_llm._client, "post", AsyncMock(return_value=mock_response)):
            result = await ollama_llm.generate_structured("Extract name", schema)

        assert result == expected


class TestOllamaFactory:
    def test_create_ollama_from_settings(self):
        from src.config import Settings
        from src.llm import create_llm

        settings = Settings(
            llm_provider="ollama", ollama_url="http://test:11434", ollama_model="phi3"
        )
        llm = create_llm(settings)
        assert isinstance(llm, OllamaLLM)
        assert llm._model == "phi3"
