import pytest

from src.config import Settings
from src.store.metadata import MetadataStore


@pytest.fixture
def test_settings(tmp_path):
    """Settings with temporary paths for testing."""
    return Settings(
        api_key="test-key",
        qdrant_url="http://localhost:6333",
        sqlite_path=tmp_path / "test.db",
        llm_provider="ollama",
    )


@pytest.fixture
async def metadata_store(tmp_path):
    """Initialized metadata store with temp SQLite."""
    store = MetadataStore()
    store.db_path = tmp_path / "test.db"
    await store.initialize()
    yield store
    await store.close()
