"""Exception handlers and error formatting utilities for API endpoints.

Provides standardized error responses for HTTP and SSE endpoints,
converting internal exceptions to appropriate HTTP status codes.
"""

from fastapi import HTTPException
from httpx import ConnectError, TimeoutException
from pydantic import ValidationError

from app.core.logging import get_logger

logger = get_logger(__name__)


def handle_llm_connection_error(
    e: ConnectError | TimeoutException,
    session_id: str,
    endpoint: str,
    method: str,
) -> HTTPException:
    """Handle LLM connection errors (ConnectError, TimeoutException).

    Args:
        e: The connection or timeout exception.
        session_id: Current session identifier for logging.
        endpoint: API endpoint path for logging context.
        method: HTTP method (GET/POST) for logging context.

    Returns:
        HTTPException with 503 status code.
    """
    logger.error(
        "%s %s sid=%s llm_connection_error: %s",
        method,
        endpoint,
        session_id,
        type(e).__name__,
    )
    return HTTPException(503, "LLM service unavailable")


def handle_validation_error(
    e: ValueError | ValidationError,
    session_id: str,
    endpoint: str,
    method: str,
) -> HTTPException:
    """Handle validation errors (ValueError, ValidationError).

    Args:
        e: The validation exception.
        session_id: Current session identifier for logging.
        endpoint: API endpoint path for logging context.
        method: HTTP method (GET/POST) for logging context.

    Returns:
        HTTPException with 400 status code.
    """
    logger.warning(
        "%s %s sid=%s validation_error: %s",
        method,
        endpoint,
        session_id,
        e,
    )
    return HTTPException(400, f"Invalid input: {e}")


def handle_unexpected_error(
    e: Exception,
    session_id: str,
    endpoint: str,
    method: str,
) -> HTTPException:
    """Handle unexpected/unknown errors.

    Args:
        e: The unexpected exception.
        session_id: Current session identifier for logging.
        endpoint: API endpoint path for logging context.
        method: HTTP method (GET/POST) for logging context.

    Returns:
        HTTPException with 500 status code.
    """
    logger.exception(
        "%s %s sid=%s unexpected_error: %s",
        method,
        endpoint,
        session_id,
        type(e).__name__,
    )
    return HTTPException(500, "Error occurred")


def format_stream_error(
    e: Exception, session_id: str, endpoint: str = "/api/chat/stream"
) -> dict:
    """Format exception as JSON payload for SSE backend-error event.

    Args:
        e: The caught exception to format.
        session_id: Current session identifier for logging.
        endpoint: API endpoint path for logging context.

    Returns:
        Dictionary with 'code' and 'message' keys suitable for JSON serialization.
    """
    method = "GET"

    if isinstance(e, (ConnectError, TimeoutException)):
        logger.error(
            "%s %s sid=%s stream_error code=llm_unavailable",
            method,
            endpoint,
            session_id,
        )
        return {"code": "llm_unavailable", "message": "LLM unavailable"}

    if isinstance(e, (ValueError, ValidationError)):
        logger.warning(
            "%s %s sid=%s stream_error code=validation_error: %s",
            method,
            endpoint,
            session_id,
            e,
        )
        return {"code": "validation_error", "message": f"Invalid: {e}"}

    logger.exception(
        "%s %s sid=%s stream_error code=unknown: %s",
        method,
        endpoint,
        session_id,
        type(e).__name__,
    )
    return {"code": "unknown_error", "message": "Error occurred"}
