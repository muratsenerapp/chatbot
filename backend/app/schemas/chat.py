from __future__ import annotations

from typing import Literal, Optional, Sequence

from pydantic import BaseModel, Field


class ChatMessageIn(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatIn(BaseModel):
    message: str = Field(..., min_length=1, description="User input")
    session_id: Optional[str] = Field(
        default=None, description="Optional session identifier to group turns."
    )
    messages: Optional[Sequence[ChatMessageIn]] = Field(
        default=None,
        description="Optional explicit conversation messages. When provided, it takes precedence over server-side memory.",
    )


class ChatOut(BaseModel):
    content: str
    session_id: Optional[str] = None
