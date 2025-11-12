"""Request/response schemas for the Chat API.

Defines minimal message and payload shapes used by the HTTP endpoints.
"""

from __future__ import annotations

from typing import Literal, Optional, Sequence

from pydantic import BaseModel, Field


class ChatMessageIn(BaseModel):
    """Single conversational turn provided by the client.

    Used when the caller wants to send an explicit conversation history instead of
    relying on server-side session memory.
    """

    role: Literal["system", "user", "assistant"]
    content: str


class ChatIn(BaseModel):
    """Chat request payload for single-shot or history-based calls.

    If `messages` is provided, the server ignores stored session memory for this call.
    Otherwise, `message` is appended to the current session and used with history.
    """

    message: str = Field(..., min_length=1, description="User input")
    session_id: Optional[str] = Field(
        default=None, description="Optional session identifier to group turns."
    )
    messages: Optional[Sequence[ChatMessageIn]] = Field(
        default=None,
        description="Optional explicit conversation messages. When provided, it takes precedence over server-side memory.",
    )


class ChatOut(BaseModel):
    """Chat response payload.

    Returns the model's full textual reply and the effective session id.
    """

    content: str
    session_id: Optional[str] = None
