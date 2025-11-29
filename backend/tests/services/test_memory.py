"""Unit tests for SessionMemory service."""

from __future__ import annotations

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.services.memory import SessionMemory


def test_session_memory_basic_flow():
    mem = SessionMemory(default_system_prompt="SYS")
    sid = "s1"
    mem.ensure_session(sid)
    assert len(mem.get_messages(sid)) == 1  # SystemMessage
    mem.append_user(sid, "hi")
    mem.append_assistant(sid, "hello")
    msgs = mem.get_messages(sid)
    assert len(msgs) == 3
    assert msgs[1].content == "hi"
    assert msgs[2].content == "hello"


def test_ensure_session_uses_default_system_prompt_once():
    """ensure_session should seed default system prompt only once."""
    memory = SessionMemory(default_system_prompt="SYS")
    session_id = "s1"

    # First call should create a single SystemMessage from default prompt
    memory.ensure_session(session_id)
    messages_first = memory.get_messages(session_id)

    assert isinstance(messages_first, tuple)
    assert len(messages_first) == 1
    assert isinstance(messages_first[0], SystemMessage)
    assert messages_first[0].content == "SYS"

    # Second call with a different prompt should be a no-op (idempotent)
    memory.ensure_session(session_id, system_prompt="OTHER")
    messages_second = memory.get_messages(session_id)

    # New snapshot object with the same contents
    assert messages_second is not messages_first
    assert messages_second == messages_first
    assert len(messages_second) == 1
    assert messages_second[0].content == "SYS"


def test_ensure_session_without_prompts_creates_empty_session():
    """ensure_session with no default/explicit prompt should give empty history."""
    memory = SessionMemory()
    session_id = "no-system"

    memory.ensure_session(session_id)
    messages = memory.get_messages(session_id)

    # No default or explicit system prompt => empty history
    assert isinstance(messages, tuple)
    assert messages == ()


def test_append_turn_creates_session_and_appends_pair():
    """append_turn should create session and append user+assistant in order."""
    memory = SessionMemory(default_system_prompt="SYS")
    session_id = "turn-session"

    memory.append_turn(session_id, "user-message", "assistant-message")

    messages = memory.get_messages(session_id)

    # Should have: System + Human + AI
    assert len(messages) == 3
    assert isinstance(messages[0], SystemMessage)
    assert isinstance(messages[1], HumanMessage)
    assert isinstance(messages[2], AIMessage)

    assert messages[0].content == "SYS"
    assert messages[1].content == "user-message"
    assert messages[2].content == "assistant-message"


def test_append_turn_does_not_duplicate_system_message_for_existing_session():
    """append_turn must not add another system message for existing session."""
    memory = SessionMemory(default_system_prompt="SYS")
    session_id = "existing-session"

    # Create session and add one user message
    memory.ensure_session(session_id)
    memory.append_user(session_id, "first-user")
    initial_messages = memory.get_messages(session_id)
    assert len(initial_messages) == 2  # System + first user

    # Append a full turn with a different system prompt
    memory.append_turn(
        session_id,
        "second-user",
        "second-assistant",
        system_prompt="OTHER",
    )

    messages = memory.get_messages(session_id)
    contents = [m.content for m in messages]

    # Still only one system message from the default prompt
    assert sum(isinstance(m, SystemMessage) for m in messages) == 1
    assert messages[0].content == "SYS"

    # Existing history plus new turn should be present
    assert "first-user" in contents
    assert "second-user" in contents
    assert "second-assistant" in contents


def test_clear_removes_all_messages_and_is_noop_for_unknown():
    """clear should drop all messages and be safe for unknown sessions."""
    memory = SessionMemory(default_system_prompt="SYS")
    session_id = "to-clear"

    # Seed some history
    memory.append_turn(session_id, "user", "assistant")
    assert len(memory.get_messages(session_id)) > 0

    # Clear should remove all messages
    memory.clear(session_id)
    messages_after_clear = memory.get_messages(session_id)
    assert messages_after_clear == ()

    # Clearing again for a non-existing session must not fail or change anything
    memory.clear(session_id)
    assert memory.get_messages(session_id) == ()


def test_session_memory_isolates_different_sessions():
    """Different session_ids must keep their histories isolated."""
    memory = SessionMemory(default_system_prompt="SYS")

    memory.append_user("s1", "hello-1")
    memory.append_assistant("s1", "world-1")

    memory.append_user("s2", "hello-2")

    msgs_s1 = memory.get_messages("s1")
    msgs_s2 = memory.get_messages("s2")

    contents_s1 = [m.content for m in msgs_s1]
    contents_s2 = [m.content for m in msgs_s2]

    # Session 1 history is independent of session 2
    assert "hello-1" in contents_s1
    assert "world-1" in contents_s1
    assert "hello-2" not in contents_s1

    # Session 2 must not see messages from session 1
    assert "hello-2" in contents_s2
    assert "hello-1" not in contents_s2
    assert "world-1" not in contents_s2


def test_get_messages_returns_immutable_snapshot():
    """get_messages should return an immutable snapshot (tuple) per call."""
    memory = SessionMemory(default_system_prompt="SYS")
    session_id = "snapshot"

    memory.append_user(session_id, "hi")
    first_snapshot = memory.get_messages(session_id)

    assert isinstance(first_snapshot, tuple)
    first_len = len(first_snapshot)

    # Mutate the underlying session by appending more messages
    memory.append_assistant(session_id, "hello")
    second_snapshot = memory.get_messages(session_id)

    # Old snapshot length does not change
    assert len(first_snapshot) == first_len
    # New snapshot reflects the updated history
    assert len(second_snapshot) > first_len
