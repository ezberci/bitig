import json

import httpx
import structlog

from src.llm.base import BaseLLM

logger = structlog.get_logger()


class OllamaLLM(BaseLLM):
    """Ollama LLM provider using the /api/generate endpoint."""

    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=120.0)

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        payload: dict = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system

        response = await self._client.post("/api/generate", json=payload)
        response.raise_for_status()
        data = response.json()
        return data["response"]

    async def generate_structured(
        self, prompt: str, schema: dict, *, system: str | None = None
    ) -> dict:
        format_instruction = (
            f"Respond ONLY with valid JSON matching this schema:\n{json.dumps(schema)}"
        )
        full_prompt = f"{prompt}\n\n{format_instruction}"

        payload: dict = {
            "model": self._model,
            "prompt": full_prompt,
            "stream": False,
            "format": "json",
        }
        if system:
            payload["system"] = system

        response = await self._client.post("/api/generate", json=payload)
        response.raise_for_status()
        data = response.json()
        return json.loads(data["response"])

    async def close(self) -> None:
        await self._client.aclose()
