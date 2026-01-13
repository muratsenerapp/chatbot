"""Message conversion utilities between various formats and LangChain messages.

Provides centralized conversion functions for:
- Raw string sequences to LangChain messages
- API schema (ChatMessageIn) objects to LangChain messages

All message conversion logic should live here to avoid DRY violations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

if TYPE_CHECKING:
    from app.schemas.chat import ChatMessageIn


def to_langchain_messages(
    user_messages: Sequence[str],
    system_prompt: str | None = None,
) -> list[BaseMessage]:
    """Convert user strings to LangChain Message objects.

    Args:
        user_messages: Sequence of user message strings to convert.
        system_prompt: Optional system prompt to prepend as SystemMessage.

    Returns:
        List of LangChain BaseMessage objects with SystemMessage (if provided)
        followed by HumanMessage instances for each user message.
    """
    messages: list[BaseMessage] = []

    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))

    for text in user_messages:
        messages.append(HumanMessage(content=text))

    return messages


def chat_messages_to_langchain(items: Sequence[ChatMessageIn]) -> list[BaseMessage]:
    """Convert API ChatMessageIn items to LangChain messages.

    Handles all three role types: system, user, and assistant.

    Args:
        items: Conversation turns in API shape, ordered oldest→newest.

    Returns:
        LangChain messages in the same order as ``items``.
    """
    out: list[BaseMessage] = []
    for m in items:
        if m.role == "system":
            out.append(SystemMessage(content=m.content))
        elif m.role == "user":
            out.append(HumanMessage(content=m.content))
        else:
            out.append(AIMessage(content=m.content))
    return out


def is_langchain_message_list(messages: Sequence) -> bool:
    """Check if sequence contains LangChain messages.

    Args:
        messages: Sequence to check for LangChain message types.

    Returns:
        True if the sequence is non-empty and the first element is a BaseMessage,
        False otherwise.
    """
    return bool(messages and isinstance(messages[0], BaseMessage))
