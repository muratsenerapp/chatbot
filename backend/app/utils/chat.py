from __future__ import annotations

from typing import List, Sequence

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage

from app.schemas.chat import ChatMessageIn


def to_lc_messages(items: Sequence[ChatMessageIn]) -> List[BaseMessage]:
    """Convert API ChatMessageIn records into LangChain BaseMessage objects."""
    out: List[BaseMessage] = []
    for m in items:
        if m.role == "system":
            out.append(SystemMessage(content=m.content))
        elif m.role == "user":
            out.append(HumanMessage(content=m.content))
        else:
            out.append(AIMessage(content=m.content))
    return out
