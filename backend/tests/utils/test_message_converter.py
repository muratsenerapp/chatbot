"""Tests for message conversion utilities."""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.schemas.chat import ChatMessageIn
from app.utils.message_converter import (
    chat_messages_to_langchain,
    is_langchain_message_list,
    to_langchain_messages,
)


def test_to_langchain_messages_simple():
    """Test converting simple strings to LangChain messages."""
    messages = to_langchain_messages(["Hello", "World"])

    assert len(messages) == 2
    assert all(isinstance(m, HumanMessage) for m in messages)
    assert messages[0].content == "Hello"
    assert messages[1].content == "World"


def test_to_langchain_messages_with_system_prompt():
    """Test converting messages with system prompt."""
    messages = to_langchain_messages(
        ["Hello", "World"], system_prompt="You are helpful"
    )

    assert len(messages) == 3
    assert isinstance(messages[0], SystemMessage)
    assert messages[0].content == "You are helpful"
    assert isinstance(messages[1], HumanMessage)
    assert messages[1].content == "Hello"
    assert isinstance(messages[2], HumanMessage)
    assert messages[2].content == "World"


def test_to_langchain_messages_empty_list():
    """Test converting empty list."""
    messages = to_langchain_messages([])
    assert len(messages) == 0


def test_to_langchain_messages_empty_with_system():
    """Test system prompt only (no user messages)."""
    messages = to_langchain_messages([], system_prompt="System only")

    assert len(messages) == 1
    assert isinstance(messages[0], SystemMessage)
    assert messages[0].content == "System only"


def test_is_langchain_message_list_true():
    """Test detecting LangChain message list."""
    messages = [
        SystemMessage(content="System"),
        HumanMessage(content="User"),
    ]

    assert is_langchain_message_list(messages) is True


def test_is_langchain_message_list_false_strings():
    """Test detecting non-LangChain list (strings)."""
    messages = ["Hello", "World"]

    assert is_langchain_message_list(messages) is False


def test_is_langchain_message_list_false_empty():
    """Test detecting empty list."""
    assert is_langchain_message_list([]) is False


def test_is_langchain_message_list_false_mixed():
    """Test detecting mixed list (should return False)."""
    messages = [
        HumanMessage(content="Valid"),
        "Invalid string",  # Not a BaseMessage
    ]

    # Should return True because first item is BaseMessage
    # (function only checks first item)
    assert is_langchain_message_list(messages) is True


def test_to_langchain_messages_preserves_order():
    """Test that message order is preserved."""
    inputs = ["First", "Second", "Third"]
    messages = to_langchain_messages(inputs, system_prompt="System")

    assert messages[0].content == "System"  # System first
    assert messages[1].content == "First"
    assert messages[2].content == "Second"
    assert messages[3].content == "Third"


# Tests for chat_messages_to_langchain (ChatMessageIn conversion)


def test_chat_messages_to_langchain_simple():
    """Test converting ChatMessageIn items to LangChain messages."""
    items = [
        ChatMessageIn(role="user", content="Hello"),
        ChatMessageIn(role="assistant", content="Hi there!"),
    ]
    messages = chat_messages_to_langchain(items)

    assert len(messages) == 2
    assert isinstance(messages[0], HumanMessage)
    assert messages[0].content == "Hello"
    assert isinstance(messages[1], AIMessage)
    assert messages[1].content == "Hi there!"


def test_chat_messages_to_langchain_with_system():
    """Test converting ChatMessageIn items including a system message."""
    items = [
        ChatMessageIn(role="system", content="You are helpful"),
        ChatMessageIn(role="user", content="Hello"),
        ChatMessageIn(role="assistant", content="Hi!"),
    ]
    messages = chat_messages_to_langchain(items)

    assert len(messages) == 3
    assert isinstance(messages[0], SystemMessage)
    assert messages[0].content == "You are helpful"
    assert isinstance(messages[1], HumanMessage)
    assert messages[1].content == "Hello"
    assert isinstance(messages[2], AIMessage)
    assert messages[2].content == "Hi!"


def test_chat_messages_to_langchain_empty():
    """Test converting empty list."""
    messages = chat_messages_to_langchain([])
    assert len(messages) == 0


def test_chat_messages_to_langchain_preserves_order():
    """Test that message order is preserved during conversion."""
    items = [
        ChatMessageIn(role="system", content="System"),
        ChatMessageIn(role="user", content="First"),
        ChatMessageIn(role="assistant", content="Response 1"),
        ChatMessageIn(role="user", content="Second"),
        ChatMessageIn(role="assistant", content="Response 2"),
    ]
    messages = chat_messages_to_langchain(items)

    assert len(messages) == 5
    assert messages[0].content == "System"
    assert messages[1].content == "First"
    assert messages[2].content == "Response 1"
    assert messages[3].content == "Second"
    assert messages[4].content == "Response 2"
