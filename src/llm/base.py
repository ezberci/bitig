from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        """Generate a text response from the LLM.

        Args:
            prompt: The user prompt.
            system: Optional system prompt.

        Returns:
            Generated text response.
        """

    @abstractmethod
    async def generate_structured(
        self, prompt: str, schema: dict, *, system: str | None = None
    ) -> dict:
        """Generate a structured (JSON) response matching the given schema.

        Args:
            prompt: The user prompt.
            schema: JSON schema the response must conform to.
            system: Optional system prompt.

        Returns:
            Parsed dict matching the schema.
        """
