from __future__ import annotations

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
