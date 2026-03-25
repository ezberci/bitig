from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # API
    api_key: str = "change-me"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "bitig"

    # LLM
    llm_provider: Literal["ollama", "claude"] = "ollama"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    claude_api_key: str | None = None

    # Embedding
    embedding_model: str = "all-MiniLM-L6-v2"

    # Storage
    sqlite_path: Path = Path("data/bitig.db")

    # Gmail
    gmail_credentials_path: Path | None = None

    # Jira
    jira_url: str | None = None
    jira_email: str | None = None
    jira_api_token: str | None = None

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 64


settings = Settings()
