"""Chat API endpoints providing single-shot replies and Server-Sent Events (SSE) token streams."""

from __future__ import annotations

import json
import time
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sse_starlette.sse import EventSourceResponse

from app.core.logging import get_logger
from app.schemas.chat import ChatIn, ChatOut
from app.services.llm_client import LLMClient
from app.services.memory import SessionMemory
from app.utils.chat import to_lc_messages
from app.utils.sessions import ensure_session_id
from app.utils.token_counter import estimate_tokens_from_iter
from langchain_core.messages import BaseMessage, HumanMessage

router = APIRouter(tags=["Chat"])
logger = get_logger("api.chat")


def get_client(request: Request) -> LLMClient:
    """Return the app-wide LLMClient; create and cache on first access.

    Args:
        request: FastAPI request whose ``app.state`` holds shared singletons.
    """
    llm_client = getattr(request.app.state, "llm_client", None)  # type: ignore[attr-defined]
    if llm_client is None:
        logger.warning(
            "llm_client missing on app.state; creating a default instance lazily."
        )
        llm_client = LLMClient()
        setattr(request.app.state, "llm_client", llm_client)  # type: ignore[attr-defined]
    return llm_client  # type: ignore[return-value]


def get_memory(request: Request) -> SessionMemory:
    """Return the session memory store; create and cache on first access.

    Seeds with the current ``LLMClient.system_prompt`` when available.

    Args:
        request: FastAPI request whose ``app.state`` holds shared singletons.
    """
    mem = getattr(request.app.state, "session_memory", None)  # type: ignore[attr-defined]
    if mem is None:
        logger.warning(
            "session_memory missing on app.state; creating SessionMemory lazily."
        )
        llm_client = getattr(request.app.state, "llm_client", None)  # type: ignore[attr-defined]
        default_prompt = (
            getattr(llm_client, "system_prompt", None) if llm_client else None
        )
        mem = SessionMemory(default_system_prompt=default_prompt)
        setattr(request.app.state, "session_memory", mem)  # type: ignore[attr-defined]
    return mem  # type: ignore[return-value]


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
    client: LLMClient = Depends(get_client),
    memory: SessionMemory = Depends(get_memory),
) -> ChatOut:
    """Return a full assistant reply in one call.

    Uses prior session history when `messages` is omitted; otherwise honors the
    explicit `messages`.

    Raises:
        HTTPException: On unexpected errors a 500 is raised, wrapping the original
            exception (see server logs for details).
    """
    start = time.perf_counter()
    sid = ensure_session_id(data.session_id)

    try:
        if data.messages:
            model_messages: list[BaseMessage] = to_lc_messages(list(data.messages))
        else:
            sys_prompt = getattr(client, "system_prompt", None)
            memory.ensure_session(sid, sys_prompt)
            history = memory.get_messages(sid)
            model_messages = history + [HumanMessage(content=data.message)]

        approx_in_tokens = estimate_tokens_from_iter([m.content for m in model_messages])  # type: ignore[attr-defined]
        try:
            num_ctx = getattr(client.llm, "model_kwargs", {}).get("num_ctx", 4096)  # type: ignore[attr-defined]
            num_predict = getattr(client.llm, "model_kwargs", {}).get("num_predict", 512)  # type: ignore[attr-defined]
        except Exception:
            num_ctx, num_predict = 4096, 512

        if approx_in_tokens > int(0.8 * num_ctx):
            logger.warning(
                "chat:input_near_limit sid=%s in~%d num_ctx=%d",
                sid,
                approx_in_tokens,
                num_ctx,
            )
        else:
            logger.debug("chat:input_tokens sid=%s in~%d", sid, approx_in_tokens)

        text = await client.ainvoke(model_messages)

        sys_prompt = getattr(client, "system_prompt", None)
        memory.append_turn(sid, data.message, text, system_prompt=sys_prompt)

        approx_out_tokens = estimate_tokens_from_iter([text])
        approx_total = approx_in_tokens + approx_out_tokens
        logger.debug(
            "chat:tokens sid=%s in~%d out~%d total~%d ctx=%d pred=%d",
            sid,
            approx_in_tokens,
            approx_out_tokens,
            approx_total,
            num_ctx,
            num_predict,
        )
        if approx_total > int(0.9 * (num_ctx + num_predict)):
            logger.warning(
                "chat:total_tokens_near_limit sid=%s total~%d (ctx=%d + pred=%d)",
                sid,
                approx_total,
                num_ctx,
                num_predict,
            )

        elapsed = (time.perf_counter() - start) * 1000
        logger.info(
            "chat:done sid=%s chars=%d elapsed_ms=%.1f", sid, len(text), elapsed
        )
        return ChatOut(content=text, session_id=sid)
    except Exception as e:  # pragma: no cover
        elapsed = (time.perf_counter() - start) * 1000
        logger.exception("chat:error sid=%s elapsed_ms=%.1f", sid, elapsed)
        raise HTTPException(status_code=500, detail="Internal server error") from e


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
    client: LLMClient = Depends(get_client),
    memory: SessionMemory = Depends(get_memory),
) -> EventSourceResponse:
    """Stream assistant tokens via SSE.

    Events: `token` (string chunk), `done` (JSON metrics), `backend-error` (string message).
    Errors are signaled via SSE events instead of HTTP errors to preserve the
    stream (per SSE semantics), so this handler does not raise on model/runtime
    failures.
    """
    start = time.perf_counter()
    sid = ensure_session_id(session_id)
    logger.info("stream:start sid=%s len=%d", sid, len(message))

    async def token_gen() -> AsyncGenerator[dict, None]:
        char_count = 0
        assistant_text_parts: list[str] = []
        try:
            sys_prompt = getattr(client, "system_prompt", None)
            memory.ensure_session(sid, sys_prompt)
            history = memory.get_messages(sid)
            model_messages: list[BaseMessage] = history + [
                HumanMessage(content=message)
            ]

            try:
                num_ctx = getattr(client.llm, "model_kwargs", {}).get("num_ctx", 4096)  # type: ignore[attr-defined]
                num_predict = getattr(client.llm, "model_kwargs", {}).get("num_predict", 512)  # type: ignore[attr-defined]
            except Exception:
                num_ctx, num_predict = 4096, 512

            approx_in_tokens = estimate_tokens_from_iter([m.content for m in model_messages])  # type: ignore[attr-defined]
            logger.debug("stream:input_tokens sid=%s in~%d", sid, approx_in_tokens)
            if approx_in_tokens > int(0.8 * num_ctx):
                logger.warning(
                    "stream:input_near_limit sid=%s in~%d num_ctx=%d",
                    sid,
                    approx_in_tokens,
                    num_ctx,
                )

            async for chunk in client.astream_chat(model_messages):
                if not chunk:
                    continue
                char_count += len(chunk)
                assistant_text_parts.append(str(chunk))
                yield {"event": "token", "data": chunk}

            full_text = "".join(assistant_text_parts)
            memory.append_turn(sid, message, full_text, system_prompt=sys_prompt)

            approx_out_tokens = estimate_tokens_from_iter(assistant_text_parts)
            approx_total = approx_in_tokens + approx_out_tokens
            logger.debug(
                "stream:tokens sid=%s in~%d out~%d total~%d ctx=%d pred=%d",
                sid,
                approx_in_tokens,
                approx_out_tokens,
                approx_total,
                num_ctx,
                num_predict,
            )
            if approx_total > int(0.9 * (num_ctx + num_predict)):
                logger.warning(
                    "stream:total_tokens_near_limit sid=%s total~%d (ctx=%d + pred=%d)",
                    sid,
                    approx_total,
                    num_ctx,
                    num_predict,
                )

            elapsed = (time.perf_counter() - start) * 1000
            metrics = {
                "session_id": sid,
                "chars": char_count,
                "elapsed_ms": round(elapsed, 1),
            }
            logger.info(
                "stream:done sid=%s chars=%d elapsed_ms=%.1f", sid, char_count, elapsed
            )
            yield {"event": "done", "data": json.dumps(metrics)}
        except Exception as e:  # keep HTTP 200 for SSE but signal error
            logger.exception("stream:error sid=%s", sid)
            yield {"event": "backend-error", "data": str(e)}

    return EventSourceResponse(token_gen())
