from fastapi import HTTPException, Request, status
from fastapi.security import APIKeyHeader

from src.config import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

OPEN_PATHS = {"/api/health", "/docs", "/openapi.json", "/redoc"}


async def verify_api_key(request: Request) -> None:
    """Verify API key from request header."""
    if request.url.path in OPEN_PATHS:
        return

    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
