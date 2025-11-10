from __future__ import annotations

import json
from contextlib import contextmanager

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessageChunk

from app.main import app
from app.api.chat import get_client

# ---- Fakes & overrides ---------------------------------------------------


class FakeOKClient:
    """OK client for success scenarios; streaming yields a couple of chunks."""

    system_prompt = "SYS"

    async def astream_chat(self, messages):
        yield "tok1"
        yield "tok2"

    async def ainvoke(self, messages):
        return "OK"


class FakeFailClient:
    """Client that fails to simulate backend errors."""

    system_prompt = "SYS"

    # IMPORTANT: Make this an async *generator* so `async for` is valid and no warning is raised.
    async def astream_chat(self, messages):
        # raise during first iteration
        raise RuntimeError("boom")
        if False:  # pragma: no cover - sentinel yield to mark as async generator
            yield ""  # never reached

    async def ainvoke(self, messages):
        raise ValueError("fail")


@contextmanager
def override_client(fake):
    app.dependency_overrides[get_client] = lambda: fake  # type: ignore
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_client, None)


# ---- Existing API tests --------------------------------------------------


def test_chat_sync_200_ok():
    with override_client(FakeOKClient()):
        c = TestClient(app)
        r = c.post(
            "/api/chat", json={"message": "Türkiye'nin başkenti?", "session_id": "t"}
        )
        assert r.status_code == 200
        body = r.json()
        assert "content" in body and isinstance(body["content"], str)
        assert body.get("session_id") == "t"


def test_chat_sync_422_validation_missing_message():
    with override_client(FakeOKClient()):
        c = TestClient(app)
        r = c.post("/api/chat", json={"session_id": "t"})  # missing message
        assert r.status_code == 422


def test_chat_sync_500_on_exception():
    with override_client(FakeFailClient()):
        c = TestClient(app)
        r = c.post("/api/chat", json={"message": "ping"})
        assert r.status_code == 500


def test_chat_stream_get_200_sse_and_done_metrics():
    with override_client(FakeOKClient()):
        c = TestClient(app)
        with c.stream(
            "GET", "/api/chat/stream", params={"message": "hello", "session_id": "sid1"}
        ) as resp:
            assert resp.status_code == 200
            assert resp.headers["content-type"].startswith("text/event-stream")
            saw_token = False
            saw_done = False
            for i, chunk in enumerate(resp.iter_lines()):
                line = chunk.decode() if isinstance(chunk, bytes) else chunk
                if line.startswith("event: token"):
                    saw_token = True
                if line.startswith("event: done"):
                    saw_done = True
                    break
                if i > 50:  # safety
                    break
            assert saw_token
            assert saw_done


def test_chat_stream_get_422_validation_missing_message():
    with override_client(FakeOKClient()):
        c = TestClient(app)
        r = c.get("/api/chat/stream")  # missing ?message
        assert r.status_code == 422


def test_chat_stream_get_backend_error_event_instead_of_500():
    with override_client(FakeFailClient()):
        c = TestClient(app)
        with c.stream("GET", "/api/chat/stream", params={"message": "hello"}) as resp:
            assert resp.status_code == 200
            saw_error = False
            for i, chunk in enumerate(resp.iter_lines()):
                line = chunk.decode() if isinstance(chunk, bytes) else chunk
                if line.startswith("event: backend-error"):
                    saw_error = True
                    break
                if i > 50:
                    break
            assert saw_error


# ---- Memory tests (moved here) ------------------------------------------


class _FakeMemModel:
    def invoke(self, messages):
        class R:
            content = f"LEN={len(messages)}"

        return R()

    async def astream(self, messages):
        yield AIMessageChunk(content=f"LEN={len(messages)}")

    async def ainvoke(self, messages):
        class R:
            content = f"LEN={len(messages)}"

        return R()


@contextmanager
def override_client_with_fake_mem():
    from app.services.llm_client import LLMClient

    app.dependency_overrides[get_client] = lambda: LLMClient(llm=_FakeMemModel())
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_client, None)


def test_chat_memory_sync_len_increases_with_session():
    with override_client_with_fake_mem():
        c = TestClient(app)
        r1 = c.post("/api/chat", json={"message": "hi"})
        assert r1.status_code == 200
        sid = r1.json()["session_id"]
        assert sid

        r2 = c.post("/api/chat", json={"message": "help", "session_id": sid})
        assert r2.status_code == 200
        assert r2.json()["content"].startswith("LEN=")
        assert int(r2.json()["content"].split("=")[1]) >= 3


def test_chat_memory_sync_explicit_messages_override_server_memory():
    with override_client_with_fake_mem():
        c = TestClient(app)
        r1 = c.post("/api/chat", json={"message": "hi"})
        sid = r1.json()["session_id"]

        r = c.post(
            "/api/chat",
            json={
                "message": "ignored",
                "session_id": sid,
                "messages": [
                    {"role": "system", "content": "You are test."},
                    {"role": "user", "content": "A?"},
                ],
            },
        )
        assert r.status_code == 200
        assert r.json()["content"] == "LEN=2"


def test_chat_stream_generates_session_and_uses_history():
    with override_client_with_fake_mem():
        c = TestClient(app)
        with c.stream("GET", "/api/chat/stream", params={"message": "hello"}) as resp:
            assert resp.status_code == 200
            saw_len = False
            new_sid = None
            for line in resp.iter_lines():
                s = line.decode() if isinstance(line, bytes) else line
                if s.startswith("data: {"):
                    metrics = json.loads(s.replace("data: ", ""))
                    new_sid = metrics.get("session_id")
                if s.startswith("data: LEN="):
                    assert int(s.rsplit("=", 1)[1]) >= 2
                    saw_len = True
            assert saw_len
            assert new_sid

        with c.stream(
            "GET",
            "/api/chat/stream",
            params={"message": "again", "session_id": new_sid},
        ) as resp2:
            assert resp2.status_code == 200
            saw_len2 = False
            for line in resp2.iter_lines():
                s = line.decode() if isinstance(line, bytes) else line
                if s.startswith("data: LEN="):
                    assert int(s.rsplit("=", 1)[1]) >= 3
                    saw_len2 = True
            assert saw_len2
