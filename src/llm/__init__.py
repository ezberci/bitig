from src.config import Settings
from src.llm.base import BaseLLM
from src.llm.claude import ClaudeLLM
from src.llm.ollama import OllamaLLM


def create_llm(settings: Settings) -> BaseLLM:
    """Create an LLM instance based on settings.

    Args:
        settings: Application settings.

    Returns:
        Configured LLM provider instance.

    Raises:
        ValueError: If provider is unknown or Claude API key is missing.
    """
    if settings.llm_provider == "ollama":
        return OllamaLLM(base_url=settings.ollama_url, model=settings.ollama_model)

    if settings.llm_provider == "claude":
        if not settings.claude_api_key:
            raise ValueError("claude_api_key is required when llm_provider is 'claude'")
        return ClaudeLLM(api_key=settings.claude_api_key)

    raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")


__all__ = ["BaseLLM", "ClaudeLLM", "OllamaLLM", "create_llm"]
