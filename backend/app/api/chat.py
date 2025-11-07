from __future__ import annotations

import asyncio
import json
import time
from typing import Optional, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.core.logging import get_logger
from app.services.llm_client import LLMClient

router = APIRouter(tags=["Chat"])
logger = get_logger("api.chat")


class ChatIn(BaseModel):
    """Request schema for non-streaming chat."""

    message: str = Field(min_length=1)
    session_id: Optional[str] = None


class ChatOut(BaseModel):
    """Response schema for non-streaming chat."""

    content: str
    session_id: Optional[str] = None


def get_client(request: Request) -> LLMClient:
    """Provide the singleton LLMClient created during app lifespan."""
    return request.app.state.llm_client


@router.post(
    "/chat",
    response_model=ChatOut,
    responses={
        200: {"description": "OK", "content": {"application/json": {}}},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"},
    },
)
async def chat(in_: ChatIn, client: LLMClient = Depends(get_client)) -> ChatOut:
    """
    Return a single, fully-formed answer (non-streaming).

    - Validates input via Pydantic (422 on invalid/missing `message`).
    - On internal errors, returns HTTP 500 (and logs exception).
    """
    start = time.perf_counter()
    sid = in_.session_id
    try:
        logger.info("chat:start sid=%s len=%d", sid or "-", len(in_.message))
        text = await client.ainvoke([in_.message])
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(
            "chat:done sid=%s len=%d elapsed_ms=%.1f", sid or "-", len(text), elapsed
        )
        return ChatOut(content=text, session_id=sid)
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        logger.exception(
            "chat:error sid=%s elapsed_ms=%.1f err=%s", sid or "-", elapsed, e
        )
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get(
    "/chat/stream",
    responses={
        200: {"description": "SSE stream", "content": {"text/event-stream": {}}},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"},
    },
)
async def chat_stream(
    message: str = Query(..., min_length=1),
    session_id: Optional[str] = None,
    client: LLMClient = Depends(get_client),
):
    """
    Server-Sent Events (SSE) stream of tokens. Use browser `EventSource`.

    Events:
      - `event: token` with a token chunk in `data`
      - `event: done` with metrics JSON in `data` (session_id, chars, elapsed_ms)
      - On backend errors, an `event: backend-error` is emitted; HTTP status stays 200
    """
    start = time.perf_counter()
    sid = session_id
    logger.info("stream:start sid=%s len=%d", sid or "-", len(message))

    async def token_gen() -> AsyncGenerator[dict, None]:
        char_count = 0
        cancelled = False
        try:
            async for t in client.astream_chat([message]):
                char_count += len(t)
                yield {"event": "token", "data": t}
        except asyncio.CancelledError:
            cancelled = True
            logger.info("stream:cancelled sid=%s", sid or "-")
            return
        except Exception as e:
            logger.exception("stream:error sid=%s err=%s", sid or "-", e)
            # Emit an SSE error event (SSE semantics: still 200 status)
            yield {"event": "backend-error", "data": "Internal server error"}
        finally:
            if cancelled:
                return
            elapsed = (time.perf_counter() - start) * 1000
            metrics = {
                "session_id": sid,
                "chars": char_count,
                "elapsed_ms": round(elapsed, 1),
            }
            logger.info(
                "stream:done sid=%s chars=%d elapsed_ms=%.1f",
                sid or "-",
                char_count,
                elapsed,
            )
            yield {"event": "done", "data": json.dumps(metrics)}

    return EventSourceResponse(token_gen())
