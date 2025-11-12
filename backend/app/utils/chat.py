"""Message conversion helpers for the Chat API.

Transforms API-facing message records into LangChain message objects.
"""

from __future__ import annotations

from typing import List, Sequence

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage

from app.schemas.chat import ChatMessageIn


def to_lc_messages(items: Sequence[ChatMessageIn]) -> List[BaseMessage]:
    """Convert API `ChatMessageIn` items to LangChain messages.

    Args:
        items: Conversation turns in API shape, ordered oldest→newest.

    Returns:
        LangChain messages in the same order as ``items``.
    """
    out: List[BaseMessage] = []
    for m in items:
        if m.role == "system":
            out.append(SystemMessage(content=m.content))
        elif m.role == "user":
            out.append(HumanMessage(content=m.content))
        else:
            out.append(AIMessage(content=m.content))
    return out
