from unittest.mock import patch

import pytest
from fastapi import HTTPException

from src.api.middleware import verify_api_key


@pytest.fixture
def mock_request():
    """Create a mock request object."""

    class MockRequest:
        def __init__(self, path: str, api_key: str | None = None):
            self.url = type("URL", (), {"path": path})()
            self.headers = {"X-API-Key": api_key} if api_key else {}

    return MockRequest


@patch("src.api.middleware.settings")
async def test_valid_api_key(mock_settings, mock_request):
    mock_settings.api_key = "secret-key"
    request = mock_request("/api/chat", api_key="secret-key")
    await verify_api_key(request)


@patch("src.api.middleware.settings")
async def test_missing_api_key(mock_settings, mock_request):
    mock_settings.api_key = "secret-key"
    request = mock_request("/api/chat")
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(request)
    assert exc_info.value.status_code == 401


@patch("src.api.middleware.settings")
async def test_invalid_api_key(mock_settings, mock_request):
    mock_settings.api_key = "secret-key"
    request = mock_request("/api/chat", api_key="wrong-key")
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(request)
    assert exc_info.value.status_code == 401


@patch("src.api.middleware.settings")
async def test_health_endpoint_skips_auth(mock_settings, mock_request):
    mock_settings.api_key = "secret-key"
    request = mock_request("/api/health")
    await verify_api_key(request)


@patch("src.api.middleware.settings")
async def test_docs_endpoint_skips_auth(mock_settings, mock_request):
    mock_settings.api_key = "secret-key"
    request = mock_request("/docs")
    await verify_api_key(request)
