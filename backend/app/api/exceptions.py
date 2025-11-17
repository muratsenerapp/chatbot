from fastapi import HTTPException
from httpx import ConnectError, TimeoutException
from pydantic import ValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)


def handle_chat_error(
    e: Exception, session_id: str, endpoint: str, method: str
) -> HTTPException:
    """Convert exceptions with full context."""

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
    """Format exception for SSE event (streaming endpoint)."""

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
