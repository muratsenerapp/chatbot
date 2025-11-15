"""Tests for ChatService business logic."""

import pytest
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.services.chat import ChatService, ChatMetrics, StreamChunk, StreamComplete
from app.services.memory import SessionMemory


class FakeLLMForService:
    """Fake LLM that returns predictable responses."""

    def __init__(self, response: str = "Test response"):
        self.system_prompt = "Test system"
        self.response = response
        self.llm = self  # Self-reference for model_kwargs access
        self.model_kwargs = {"num_ctx": 4096, "num_predict": 512}

    async def ainvoke(self, messages):
        """Return fixed response."""
        return self.response

    async def astream_chat(self, messages):
        """Stream response character by character."""
        for char in self.response:
            yield char


@pytest.fixture
def fake_llm():
    """Provide a fake LLM client."""
    return FakeLLMForService()


@pytest.fixture
def memory():
    """Provide a fresh SessionMemory instance."""
    return SessionMemory(default_system_prompt="Test system")


@pytest.fixture
def chat_service(fake_llm, memory):
    """Provide a ChatService with fake dependencies."""
    return ChatService(llm_client=fake_llm, memory=memory)


# ---- process_message Tests ----


@pytest.mark.asyncio
async def test_process_message_basic(chat_service):
    """Test basic message processing."""
    response, metrics = await chat_service.process_message(
        message="Hello", session_id="test-session"
    )

    assert response == "Test response"
    assert isinstance(metrics, ChatMetrics)
    assert metrics.input_tokens > 0
    assert metrics.output_tokens > 0
    assert metrics.total_tokens > 0
    assert metrics.elapsed_ms >= 0


@pytest.mark.asyncio
async def test_process_message_updates_memory(chat_service, memory):
    """Test that processing updates session memory."""
    session_id = "test-session"

    # Initial state - no messages
    assert len(memory.get_messages(session_id)) == 0

    # Process first message
    await chat_service.process_message(message="Hello", session_id=session_id)

    # Should have: system + user + assistant
    messages = memory.get_messages(session_id)
    assert len(messages) >= 2  # At least user + assistant
    assert any(isinstance(m, HumanMessage) for m in messages)
    assert any(isinstance(m, AIMessage) for m in messages)


@pytest.mark.asyncio
async def test_process_message_accumulates_history(chat_service, memory):
    """Test that multiple messages accumulate in session."""
    session_id = "test-session"

    # First message
    await chat_service.process_message("First", session_id)
    count_after_first = len(memory.get_messages(session_id))

    # Second message
    await chat_service.process_message("Second", session_id)
    count_after_second = len(memory.get_messages(session_id))

    # Should have more messages after second call
    assert count_after_second > count_after_first


@pytest.mark.asyncio
async def test_process_message_with_explicit_messages(chat_service, memory):
    """Test that explicit messages override session memory."""
    session_id = "test-session"

    # Create session with some history
    await chat_service.process_message("Ignored", session_id)

    # Use explicit messages (should override history)
    explicit = [
        SystemMessage(content="Custom system"),
        HumanMessage(content="Custom user"),
    ]

    response, metrics = await chat_service.process_message(
        message="Also ignored", session_id=session_id, explicit_messages=explicit
    )

    # Response should be based on explicit messages
    assert response == "Test response"

    # Session memory should NOT be updated when using explicit messages
    # (history should still have the first message only)
    messages = memory.get_messages(session_id)
    # Should not contain "Also ignored" since we used explicit messages
    content_list = [m.content for m in messages]
    assert "Also ignored" not in content_list


@pytest.mark.asyncio
async def test_process_message_metrics_structure(chat_service):
    """Test that metrics have correct structure."""
    _, metrics = await chat_service.process_message(message="Test", session_id="test")

    assert hasattr(metrics, "input_tokens")
    assert hasattr(metrics, "output_tokens")
    assert hasattr(metrics, "total_tokens")
    assert hasattr(metrics, "elapsed_ms")
    assert hasattr(metrics, "is_near_limit")

    assert isinstance(metrics.input_tokens, int)
    assert isinstance(metrics.output_tokens, int)
    assert isinstance(metrics.total_tokens, int)
    assert isinstance(metrics.elapsed_ms, float)
    assert isinstance(metrics.is_near_limit, bool)


@pytest.mark.asyncio
async def test_process_message_total_tokens_calculation(chat_service):
    """Test that total tokens equals input + output."""
    _, metrics = await chat_service.process_message(message="Test", session_id="test")

    assert metrics.total_tokens == metrics.input_tokens + metrics.output_tokens


# ---- process_message_stream Tests ----


@pytest.mark.asyncio
async def test_process_message_stream_basic(chat_service):
    """Test basic streaming functionality."""
    chunks = []
    completion = None

    async for item in chat_service.process_message_stream(
        message="Hello", session_id="test-stream"
    ):
        if isinstance(item, StreamChunk):
            chunks.append(item)
        elif isinstance(item, StreamComplete):
            completion = item

    # Should have received chunks
    assert len(chunks) > 0
    # Should have received completion
    assert completion is not None

    # Reconstruct response from chunks
    full_response = "".join(chunk.token for chunk in chunks)
    assert full_response == "Test response"


@pytest.mark.asyncio
async def test_process_message_stream_chunk_structure(chat_service):
    """Test StreamChunk structure."""
    first_chunk = None

    async for item in chat_service.process_message_stream(
        message="Test", session_id="test"
    ):
        if isinstance(item, StreamChunk):
            first_chunk = item
            break

    assert first_chunk is not None
    assert hasattr(first_chunk, "token")
    assert hasattr(first_chunk, "char_count")
    assert isinstance(first_chunk.token, str)
    assert isinstance(first_chunk.char_count, int)
    assert first_chunk.char_count > 0


@pytest.mark.asyncio
async def test_process_message_stream_completion_structure(chat_service):
    """Test StreamComplete structure."""
    completion = None

    async for item in chat_service.process_message_stream(
        message="Test", session_id="test"
    ):
        if isinstance(item, StreamComplete):
            completion = item

    assert completion is not None
    assert hasattr(completion, "session_id")
    assert hasattr(completion, "total_chars")
    assert hasattr(completion, "metrics")

    assert completion.session_id == "test"
    assert isinstance(completion.total_chars, int)
    assert isinstance(completion.metrics, ChatMetrics)


@pytest.mark.asyncio
async def test_process_message_stream_updates_memory(chat_service, memory):
    """Test that streaming updates memory."""
    session_id = "test-stream"

    # Process stream
    async for item in chat_service.process_message_stream(
        message="Hello", session_id=session_id
    ):
        pass  # Consume all items

    # Memory should be updated
    messages = memory.get_messages(session_id)
    assert len(messages) > 0
    assert any(isinstance(m, HumanMessage) for m in messages)
    assert any(isinstance(m, AIMessage) for m in messages)


@pytest.mark.asyncio
async def test_process_message_stream_char_count_increases(chat_service):
    """Test that char_count increases with each chunk."""
    prev_count = 0

    async for item in chat_service.process_message_stream(
        message="Test", session_id="test"
    ):
        if isinstance(item, StreamChunk):
            assert item.char_count > prev_count
            prev_count = item.char_count


@pytest.mark.asyncio
async def test_process_message_stream_total_chars_matches(chat_service):
    """Test that total_chars in completion matches sum of chunks."""
    total_from_chunks = 0
    completion = None

    async for item in chat_service.process_message_stream(
        message="Test", session_id="test"
    ):
        if isinstance(item, StreamChunk):
            total_from_chunks += len(item.token)
        elif isinstance(item, StreamComplete):
            completion = item

    assert completion.total_chars == total_from_chunks


# ---- Context Window Tests ----


@pytest.mark.asyncio
async def test_get_context_settings(chat_service):
    """Test context settings extraction."""
    num_ctx, num_predict = chat_service._get_context_settings()

    assert isinstance(num_ctx, int)
    assert isinstance(num_predict, int)
    assert num_ctx > 0
    assert num_predict > 0


@pytest.mark.asyncio
async def test_get_context_settings_defaults():
    """Test context settings fallback to defaults."""

    # Create LLM without model_kwargs
    class MinimalLLM:
        system_prompt = "Test"
        llm = None  # No model_kwargs available

        async def ainvoke(self, messages):
            return "Response"

        async def astream_chat(self, messages):
            yield "R"

    service = ChatService(llm_client=MinimalLLM(), memory=SessionMemory())

    num_ctx, num_predict = service._get_context_settings()

    # Should use defaults
    assert num_ctx == 4096
    assert num_predict == 512


# ---- Edge Cases ----


@pytest.mark.asyncio
async def test_process_message_empty_response():
    """Test handling of empty LLM response."""

    class EmptyLLM:
        system_prompt = "Test"
        llm = type("obj", (object,), {"model_kwargs": {}})

        async def ainvoke(self, messages):
            return ""

    service = ChatService(llm_client=EmptyLLM(), memory=SessionMemory())

    response, metrics = await service.process_message("Test", "session")

    assert response == ""
    assert metrics.output_tokens >= 0


@pytest.mark.asyncio
async def test_multiple_sessions_independent():
    """Test that different sessions are independent."""
    fake_llm = FakeLLMForService()
    memory = SessionMemory()
    service = ChatService(llm_client=fake_llm, memory=memory)

    # Process messages in different sessions
    await service.process_message("Session1 msg", "session-1")
    await service.process_message("Session2 msg", "session-2")

    # Sessions should be independent
    messages_1 = memory.get_messages("session-1")
    messages_2 = memory.get_messages("session-2")

    # Each should have their own messages
    content_1 = [m.content for m in messages_1]
    content_2 = [m.content for m in messages_2]

    assert "Session1 msg" in content_1
    assert "Session1 msg" not in content_2
    assert "Session2 msg" in content_2
    assert "Session2 msg" not in content_1
