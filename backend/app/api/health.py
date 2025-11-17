"""Health-check API router."""

from fastapi import APIRouter, Request

from app.core.logging import get_logger

router = APIRouter(tags=["Health"])
logger = get_logger("api.chat")


@router.get("/health", summary="Health check endpoint")
async def health_check(request: Request) -> dict:
    """Health check endpoint.

    This endpoint verifies that the FastAPI application is running and able to
    handle requests. It relies on the shared application logger that is set in
    ``app.state`` during the startup phase (inside the lifespan context).

    Args:
        request (Request): The incoming FastAPI request object. Used to access
            the global logger stored in ``request.app.state.logger``.

    Returns:
        dict: A JSON object containing a basic service status and metadata.

    Example:
        GET /api/health
        {
            "status": "ok",
            "service": "chatbot-backend"
        }
    """
    logger.debug("Health check endpoint called.")
    logger.info("Health check successful.")

    return {"status": "ok", "service": "chatbot-backend"}
