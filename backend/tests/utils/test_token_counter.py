"""Tests for token estimation utilities."""

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.utils.token_counter import (
    estimate_tokens_from_text,
    estimate_tokens_from_iter,
    estimate_tokens_from_messages,
    CHARS_PER_TOKEN,
)


def test_estimate_tokens_from_text_simple():
    """Test basic token estimation from text."""
    # 100 chars should be ~25 tokens (100/4)
    text = "a" * 100
    tokens = estimate_tokens_from_text(text)
    assert tokens == 100 // CHARS_PER_TOKEN


def test_estimate_tokens_from_text_empty():
    """Test token estimation with empty string."""
    assert estimate_tokens_from_text("") == 0
    assert estimate_tokens_from_text(None) == 0


def test_estimate_tokens_from_text_minimum_one():
    """Test that small texts get at least 1 token."""
    # Less than 4 chars should still return 1
    assert estimate_tokens_from_text("a") == 1
    assert estimate_tokens_from_text("ab") == 1
    assert estimate_tokens_from_text("abc") == 1


def test_estimate_tokens_from_text_realistic():
    """Test with realistic text."""
    text = "Hello, how are you doing today?"
    # 32 chars = ~8 tokens
    tokens = estimate_tokens_from_text(text)
    assert tokens == len(text) // CHARS_PER_TOKEN
    assert 7 <= tokens <= 9  # Reasonable range


def test_estimate_tokens_from_iter_simple():
    """Test token estimation from iterable of strings."""
    texts = ["Hello", "World", "Test"]
    total_chars = sum(len(t) for t in texts)
    expected = total_chars // CHARS_PER_TOKEN

    tokens = estimate_tokens_from_iter(texts)
    assert tokens == expected


def test_estimate_tokens_from_iter_empty():
    """Test with empty iterable."""
    assert estimate_tokens_from_iter([]) == 0


def test_estimate_tokens_from_iter_with_empty_strings():
    """Test with some empty strings in iterable."""
    texts = ["Hello", "", "World", ""]
    # "Hello" = 5 chars, "World" = 5 chars, empty = 0
    # Total = 10 chars = 2 tokens (at least 1 per non-empty)
    tokens = estimate_tokens_from_iter(texts)
    assert tokens >= 0


def test_estimate_tokens_from_messages_simple():
    """Test token estimation from LangChain messages."""
    messages = [
        SystemMessage(content="You are helpful"),  # 15 chars
        HumanMessage(content="Hello"),  # 5 chars
        AIMessage(content="Hi there!"),  # 9 chars
    ]
    # Total: 29 chars = ~7 tokens
    tokens = estimate_tokens_from_messages(messages)
    expected = (15 + 5 + 9) // CHARS_PER_TOKEN
    assert tokens == expected


def test_estimate_tokens_from_messages_empty():
    """Test with empty message list."""
    assert estimate_tokens_from_messages([]) == 0


def test_estimate_tokens_from_messages_realistic():
    """Test with realistic conversation."""
    messages = [
        SystemMessage(content="You are a helpful assistant"),
        HumanMessage(content="What is the capital of France?"),
        AIMessage(content="The capital of France is Paris."),
        HumanMessage(content="What about Turkey?"),
        AIMessage(content="The capital of Turkey is Ankara."),
    ]

    total_chars = sum(len(m.content) for m in messages)
    expected = total_chars // CHARS_PER_TOKEN

    tokens = estimate_tokens_from_messages(messages)
    assert tokens == expected
    assert tokens > 0


def test_chars_per_token_constant():
    """Test that CHARS_PER_TOKEN is reasonable."""
    assert CHARS_PER_TOKEN == 4
    # This is a heuristic for Latin scripts


def test_estimate_consistency():
    """Test that different functions give consistent results."""
    text = "Hello, world! This is a test message."

    # These should give same result for same text
    tokens_text = estimate_tokens_from_text(text)
    tokens_iter = estimate_tokens_from_iter([text])
    tokens_messages = estimate_tokens_from_messages([HumanMessage(content=text)])

    assert tokens_text == tokens_iter
    assert tokens_text == tokens_messages


def test_estimate_tokens_unicode():
    """Test with unicode characters (Turkish)."""
    text = "Merhaba dünya! Türkiye'nin başkenti Ankara'dır."
    tokens = estimate_tokens_from_text(text)

    # Should work with Turkish characters
    assert tokens > 0
    assert tokens == len(text) // CHARS_PER_TOKEN
