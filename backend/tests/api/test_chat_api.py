from __future__ import annotations

from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.main import app
from app.api.chat import get_client
from app.services.llm_client import LLMClient


class FakeOKClient(LLMClient):
    """Fake client that returns a fixed response and a short token stream."""

    def __init__(self):  # no real LLM inside
        pass

    async def astream_chat(self, user_messages, system_prompt=None):
        # Proper async generator: yields small chunks
        for ch in ["An", "ka", "ra"]:
            yield ch

    async def ainvoke(self, user_messages, system_prompt=None) -> str:
        return "Ankara"


class FakeFailClient(LLMClient):
    """Fake client that raises exceptions (sync & streaming)."""

    def __init__(self):
        pass

    async def astream_chat(self, user_messages, system_prompt=None):
        # Make this an async *generator* (so `async for` is valid)
        if False:  # pragma: no cover
            yield ""  # ensures function is treated as an async generator
        raise RuntimeError("boom in stream")

    async def ainvoke(self, user_messages, system_prompt=None) -> str:
        raise RuntimeError("boom in sync")


@contextmanager
def override_client(fake):
    app.dependency_overrides[get_client] = lambda: fake
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_client, None)


def test_chat_sync_200_ok():
    with override_client(FakeOKClient()):
        c = TestClient(app)
        r = c.post(
            "/api/chat", json={"message": "Türkiye'nin başkenti?", "session_id": "t"}
        )
        assert r.status_code == 200
        data = r.json()
        assert data["content"] == "Ankara"
        assert data["session_id"] == "t"


def test_chat_sync_422_validation_missing_message():
    with override_client(FakeOKClient()):
        c = TestClient(app)
        # missing 'message'
        r = c.post("/api/chat", json={"session_id": "t"})
        assert r.status_code == 422

    with override_client(FakeOKClient()):
        c = TestClient(app)
        # empty message -> min_length=1 triggers 422
        r = c.post("/api/chat", json={"message": "", "session_id": "t"})
        assert r.status_code == 422


def test_chat_sync_500_on_exception():
    with override_client(FakeFailClient()):
        c = TestClient(app)
        r = c.post("/api/chat", json={"message": "ping"})
        assert r.status_code == 500
        body = r.json()
        assert body["detail"] == "Internal server error"


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
                if i > 50:  # safety break
                    break
            assert saw_token
            assert saw_done


def test_chat_stream_get_422_validation_missing_message():
    with override_client(FakeOKClient()):
        c = TestClient(app)
        r = c.get("/api/chat/stream")  # missing ?message
        assert r.status_code == 422


def test_chat_stream_get_error_event_instead_of_500():
    # For SSE, we emit an 'error' event but keep HTTP 200 per SSE semantics.
    with override_client(FakeFailClient()):
        c = TestClient(app)
        with c.stream("GET", "/api/chat/stream", params={"message": "hello"}) as resp:
            assert resp.status_code == 200
            saw_error = False
            for i, chunk in enumerate(resp.iter_lines()):
                line = chunk.decode() if isinstance(chunk, bytes) else chunk
                if line.startswith("event: error"):
                    saw_error = True
                    break
                if i > 50:  # safety break
                    break
            assert saw_error
