"""Chat API endpoints providing single-shot replies and Server-Sent Events (SSE) token streams."""

from __future__ import annotations

import json
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, Query, Request
from sse_starlette.sse import EventSourceResponse

from app.api.exceptions import handle_chat_error, format_stream_error
from app.core.logging import get_logger
from app.schemas.chat import ChatIn, ChatOut
from app.services.chat import ChatService, StreamChunk, StreamComplete
from app.utils.chat import to_lc_messages
from app.utils.sessions import ensure_session_id

router = APIRouter(tags=["Chat"])
logger = get_logger(__name__)


def get_chat_service(
    request: Request,
) -> ChatService:
    """Get or create a ChatService instance.

    The service is created lazily on first access and cached in app.state
    to avoid repeated initialization.

    Args:
        request: FastAPI request providing access to app state.

    Returns:
        ChatService instance ready for processing chat requests.

    Raises:
        RuntimeError: If application dependencies (llm_client, session_memory)
            are not initialized in app.state.
    """
    service = getattr(request.app.state, "chat_service", None)

    if service is None:
        logger.info("Creating ChatService instance")

        # Get dependencies
        llm_client = getattr(request.app.state, "llm_client", None)
        memory = getattr(request.app.state, "session_memory", None)

        if not llm_client or not memory:
            raise RuntimeError("Application dependencies not initialized")

        # Create and cache service
        service = ChatService(
            llm_client=llm_client,
            memory=memory,
        )
        setattr(request.app.state, "chat_service", service)

    return service


@router.post(
    "/chat",
    response_model=ChatOut,
    summary="Single-shot chat completion",
    description=(
        "Generates a single response using the current session history (if any) "
        "or explicit messages supplied in the request body."
    ),
    responses={
        200: {"description": "OK"},
        500: {"description": "Internal server error"},
    },
)
async def chat_sync(
    data: ChatIn,
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatOut:
    """Single-shot chat completion.

    Args:
        data: Chat request containing user message and optional session/messages.
        chat_service: Injected ChatService dependency.

    Returns:
        ChatOut containing assistant response and session ID.

    Raises:
        HTTPException: 503 if LLM service is unavailable, 400 for invalid
            input payloads, or 500 for unexpected errors.
    """
    sid = ensure_session_id(data.session_id)

    try:
        response, metrics = await chat_service.process_message(
            message=data.message,
            session_id=sid,
            explicit_messages=to_lc_messages(data.messages) if data.messages else None,
        )

        logger.info(
            f"chat:done sid={sid} chars={len(response)} "
            f"elapsed_ms={metrics.elapsed_ms:.1f}"
        )

        if metrics.is_near_limit:
            logger.warning(f"chat:near_limit sid={sid} total={metrics.total_tokens}")

        return ChatOut(content=response, session_id=sid)

    except Exception as e:
        raise handle_chat_error(e, sid, endpoint="/api/chat", method="POST") from e


@router.get(
    "/chat/stream",
    summary="SSE token stream",
    description=(
        "Streams tokens over Server-Sent Events. Emits `token` events for chunks, "
        "`done` with basic metrics on completion, and `backend-error` on failures "
        "(HTTP 200 is kept per SSE semantics)."
    ),
    responses={
        200: {
            "description": "Event stream of tokens and terminal events.",
            "content": {"text/event-stream": {}},
        }
    },
)
async def chat_stream_get(
    message: str = Query(..., min_length=1),
    session_id: Optional[str] = Query(default=None),
    service: ChatService = Depends(get_chat_service),
) -> EventSourceResponse:
    """Stream assistant tokens via SSE.

    Events: `token` (string chunk), `done` (JSON metrics), `backend-error` (string message).
    Errors are signaled via SSE events instead of HTTP errors to preserve the
    stream (per SSE semantics), so this handler does not raise on model/runtime
    failures.

    Args:
        message: User input text (query parameter).
        session_id: Optional session identifier (query parameter).
        service: Injected ChatService dependency.

    Returns:
        EventSourceResponse streaming SSE events.
    """
    sid = ensure_session_id(session_id)
    logger.info(f"stream:start sid={sid} len={len(message)}")

    async def token_gen() -> AsyncGenerator[dict, None]:
        """Generate SSE events from the ChatService stream."""
        try:
            async for item in service.process_message_stream(
                message=message,
                session_id=sid,
            ):
                if isinstance(item, StreamChunk):
                    # Yield token event
                    yield {"event": "token", "data": item.token}

                elif isinstance(item, StreamComplete):
                    # Yield done event with metrics
                    metrics = {
                        "session_id": item.session_id,
                        "chars": item.total_chars,
                        "elapsed_ms": round(item.metrics.elapsed_ms, 1),
                    }
                    yield {"event": "done", "data": json.dumps(metrics)}

        except Exception as e:
            error_data = format_stream_error(e, sid, endpoint="/api/chat/stream")
            yield {"event": "backend-error", "data": json.dumps(error_data)}

    return EventSourceResponse(token_gen())
