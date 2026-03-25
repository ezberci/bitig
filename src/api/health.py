import httpx
import structlog
from fastapi import APIRouter

from src.config import settings

router = APIRouter()
logger = structlog.get_logger()


@router.get("/health")
async def health_check() -> dict:
    """Check health of all services."""
    checks: dict[str, str] = {}

    # Check Qdrant
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.qdrant_url}/healthz")
            checks["qdrant"] = "ok" if resp.status_code == 200 else "error"
    except httpx.RequestError:
        checks["qdrant"] = "unreachable"

    # Check Ollama (if configured)
    if settings.llm_provider == "ollama":
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{settings.ollama_url}/api/tags")
                checks["ollama"] = "ok" if resp.status_code == 200 else "error"
        except httpx.RequestError:
            checks["ollama"] = "unreachable"

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "healthy" if all_ok else "degraded", "services": checks}
