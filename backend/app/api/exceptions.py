"""Exception handlers and error formatting utilities for API endpoints.

Provides standardized error responses for HTTP and SSE endpoints,
converting internal exceptions to appropriate HTTP status codes.
"""

from fastapi import HTTPException
from httpx import ConnectError, TimeoutException
from pydantic import ValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)


def handle_chat_error(
    e: Exception, session_id: str, endpoint: str, method: str
) -> HTTPException:
    """Convert exceptions to appropriate HTTPException with full context.

    Maps different exception types to HTTP status codes:
    - ConnectError/TimeoutException -> 503
    - ValueError/ValidationError -> 400
    - Other exceptions -> 500

    Args:
        e: The caught exception to convert.
        session_id: Current session identifier for logging.
        endpoint: API endpoint path for logging context.
        method: HTTP method (GET/POST) for logging context.

    Returns:
        HTTPException with appropriate status code and message.
    """

    # Full context prefix
    log_prefix = _build_log_prefix(
        session_id=session_id,
        endpoint=endpoint,
        method=method,
    )

    if isinstance(e, (ConnectError, TimeoutException)):
        logger.error(f"{log_prefix} llm_connection_error")
        return HTTPException(503, "LLM service unavailable")

    if isinstance(e, (ValueError, ValidationError)):
        logger.warning(f"{log_prefix} validation_error: {e}")
        return HTTPException(400, f"Invalid input: {e}")

    logger.exception(f"{log_prefix} unexpected_error")
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

    log_prefix = _build_log_prefix(
        session_id=session_id,
        endpoint=endpoint,
        method="GET",
    )

    if isinstance(e, (ConnectError, TimeoutException)):
        logger.error(f"{log_prefix} stream_error code=llm_unavailable")
        return {"code": "llm_unavailable", "message": "LLM unavailable"}

    if isinstance(e, (ValueError, ValidationError)):
        logger.warning(f"{log_prefix} stream_error code=validation_error")
        return {"code": "validation_error", "message": f"Invalid: {e}"}

    logger.exception(f"{log_prefix} stream_error code=unknown")
    return {"code": "unknown_error", "message": "Error occurred"}


def _build_log_prefix(
    *,
    session_id: str,
    endpoint: str,
    method: str,
) -> str:
    """Consistent log prefix for API errors."""
    return f"{method} {endpoint} sid={session_id}"
