"""Health-check API router."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Request

from app.core.logging import get_logger

router = APIRouter(tags=["Health"])
logger = get_logger(__name__)

# Timeout for Ollama health check (seconds)
OLLAMA_HEALTH_TIMEOUT = 5.0


async def check_ollama_connection(base_url: str) -> bool:
    """Check if Ollama server is reachable and responding.

    Makes a lightweight GET request to the Ollama API root endpoint.

    Args:
        base_url: The Ollama server base URL (e.g., http://localhost:11434).

    Returns:
        True if Ollama is reachable and responding, False otherwise.
    """
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_HEALTH_TIMEOUT) as client:
            # Ollama root endpoint returns "Ollama is running"
            response = await client.get(base_url)
            return response.status_code == 200
    except (httpx.RequestError, httpx.TimeoutException) as e:
        logger.warning("Ollama health check failed: %s", e)
        return False


@router.get("/health", summary="Health check endpoint")
async def health_check(request: Request) -> dict:
    """Health check endpoint with dependency status.

    This endpoint verifies that the FastAPI application is running and checks
    the health of external dependencies (Ollama). Returns a degraded status
    if any dependency is unavailable.

    Args:
        request (Request): The incoming FastAPI request object. Used to access
            application settings from ``request.app.state.settings``.

    Returns:
        dict: A JSON object containing service status, metadata, and dependency health.

    Example:
        GET /api/health
        {
            "status": "ok",
            "service": "chatbot-backend",
            "dependencies": {
                "ollama": "ok"
            }
        }

        # When Ollama is unavailable:
        {
            "status": "degraded",
            "service": "chatbot-backend",
            "dependencies": {
                "ollama": "unavailable"
            }
        }
    """
    logger.debug("Health check endpoint called.")

    # Get Ollama base URL from settings
    settings = getattr(request.app.state, "settings", None)
    ollama_base_url = settings.OLLAMA_BASE_URL if settings else "http://localhost:11434"

    # Check Ollama connection
    ollama_ok = await check_ollama_connection(ollama_base_url)
    ollama_status = "ok" if ollama_ok else "unavailable"

    # Overall status is degraded if any dependency is down
    overall_status = "ok" if ollama_ok else "degraded"

    logger.info(
        "Health check completed: status=%s ollama=%s",
        overall_status,
        ollama_status,
    )

    return {
        "status": overall_status,
        "service": "chatbot-backend",
        "dependencies": {
            "ollama": ollama_status,
        },
    }
