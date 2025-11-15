from typing import Sequence, Optional
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage


def to_langchain_messages(
    user_messages: Sequence[str],
    system_prompt: Optional[str] = None,
) -> list[BaseMessage]:
    """Convert user strings to LangChain Message objects."""
    messages: list[BaseMessage] = []

    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))

    for text in user_messages:
        messages.append(HumanMessage(content=text))

    return messages


def is_langchain_message_list(messages: Sequence) -> bool:
    """Check if sequence contains LangChain messages."""
    # FIX: Ensure we return bool, not the list itself
    return bool(messages and isinstance(messages[0], BaseMessage))
