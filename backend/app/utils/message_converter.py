"""Message conversion utilities between string sequences and LangChain messages.

Handles bidirectional conversion for LLM communication layer.
"""

from typing import Sequence, Optional
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage


def to_langchain_messages(
    user_messages: Sequence[str],
    system_prompt: Optional[str] = None,
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


def is_langchain_message_list(messages: Sequence) -> bool:
    """Check if sequence contains LangChain messages.

    Args:
        messages: Sequence to check for LangChain message types.

    Returns:
        True if the sequence is non-empty and the first element is a BaseMessage,
        False otherwise.
    """
    return bool(messages and isinstance(messages[0], BaseMessage))
