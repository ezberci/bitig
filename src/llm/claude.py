import json

import structlog
from anthropic import AsyncAnthropic

from src.llm.base import BaseLLM

logger = structlog.get_logger()


class ClaudeLLM(BaseLLM):
    """Claude LLM provider using the Anthropic API."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        kwargs: dict = {
            "model": self._model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        response = await self._client.messages.create(**kwargs)
        return response.content[0].text

    async def generate_structured(
        self, prompt: str, schema: dict, *, system: str | None = None
    ) -> dict:
        format_instruction = (
            f"Respond ONLY with valid JSON matching this schema:\n{json.dumps(schema)}"
        )
        full_prompt = f"{prompt}\n\n{format_instruction}"

        kwargs: dict = {
            "model": self._model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": full_prompt}],
        }
        if system:
            kwargs["system"] = system

        response = await self._client.messages.create(**kwargs)
        return json.loads(response.content[0].text)

    async def close(self) -> None:
        await self._client.close()
