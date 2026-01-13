"""API endpoint tests for chat routes."""

from __future__ import annotations

import json
from contextlib import contextmanager

from fastapi.testclient import TestClient
from httpx import ConnectError, TimeoutException
from langchain_core.messages import AIMessageChunk

from app.main import app
from app.api.chat import get_chat_service
from app.services.chat import ChatService
from app.services.llm import LLMClient
from app.services.memory import SessionMemory


# ---- Fakes & overrides ---------------------------------------------------


class HasContextLimitsMixin:
    """Test helper mixin to satisfy ChatService LLM interface."""

    def get_context_limits(
        self,
        *,
        default_ctx: int = 4096,
        default_num_predict: int = 512,
    ) -> tuple[int, int]:
        return default_ctx, default_num_predict


class FakeOKClient(HasContextLimitsMixin):
    """OK client for success scenarios; streaming yields a couple of chunks."""

    system_prompt = "SYS"

    async def astream_chat(self, messages):
        yield "tok1"
        yield "tok2"

    async def ainvoke(self, messages):
        return "OK"


class FakeFailClient(HasContextLimitsMixin):
    """Client that fails with a generic backend error (maps to HTTP 500)."""

    system_prompt = "SYS"

    async def astream_chat(self, messages):
        # Async generator that fails on first iteration.
        yield "partial"
        raise RuntimeError("boom")

    async def ainvoke(self, messages):
        # Generic backend failure
        raise RuntimeError("fail")


class FakeValidationErrorClient(HasContextLimitsMixin):
    """Client that raises ValueError to simulate validation-like errors (400)."""

    system_prompt = "SYS"

    async def astream_chat(self, messages):
        yield "partial"
        raise ValueError("invalid")

    async def ainvoke(self, messages):
        raise ValueError("invalid")


class FakeUnavailableClient(HasContextLimitsMixin):
    """Client that simulates LLM connectivity issues (503)."""

    system_prompt = "SYS"

    async def astream_chat(self, messages):
        yield "partial"
        raise ConnectError("llm unavailable")

    async def ainvoke(self, messages):
        raise ConnectError("llm unavailable")


class FakeTimeoutClient(HasContextLimitsMixin):
    """Client that simulates LLM timeouts (TimeoutException -> 503)."""

    system_prompt = "SYS"

    async def astream_chat(self, messages):
        # Simulate partial stream, then a timeout from the LLM
        yield "partial"
        raise TimeoutException("llm timeout")

    async def ainvoke(self, messages):
        # For sync endpoint, this would also behave as a timeout
        raise TimeoutException("llm timeout")


@contextmanager
def override_chat_service(fake_client):
    """Override ChatService with a fake LLM client."""
    memory = SessionMemory(default_system_prompt="SYS")
    service = ChatService(llm_client=fake_client, memory=memory)

    app.dependency_overrides[get_chat_service] = lambda: service
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_chat_service, None)


# ----- Helpers ---------------------------------------------------------


def _read_backend_error_payload(fake_client, params: dict[str, str]) -> dict:
    """Read backend-error SSE event and decode its JSON payload.

    This helper:
    - calls /api/chat/stream with the given params,
    - finds the `event: backend-error` line,
    - reads the first following `data:` line,
    - parses JSON and returns the resulting dict.
    """
    with override_chat_service(fake_client):
        c = TestClient(app)
        with c.stream("GET", "/api/chat/stream", params=params) as resp:
            assert resp.status_code == 200

            saw_error = False
            data_line: str | None = None

            for i, chunk in enumerate(resp.iter_lines()):
                line = chunk.decode() if isinstance(chunk, bytes) else chunk

                if line.startswith("event: backend-error"):
                    saw_error = True
                    continue

                if saw_error and line.startswith("data: "):
                    data_line = line[len("data: ") :].strip()
                    break

                if i > 200:  # safety
                    break

            assert data_line is not None, "backend-error event payload not found"

            return json.loads(data_line)


# ---- Existing API tests --------------------------------------------------


def test_chat_sync_200_ok():
    """Test successful chat response."""
    with override_chat_service(FakeOKClient()):
        c = TestClient(app)
        r = c.post(
            "/api/chat", json={"message": "Türkiye'nin başkenti?", "session_id": "t"}
        )
        assert r.status_code == 200
        body = r.json()
        assert "content" in body and isinstance(body["content"], str)
        assert body.get("session_id") == "t"


def test_chat_sync_422_validation_missing_message():
    """Test validation error when message is missing."""
    with override_chat_service(FakeOKClient()):
        c = TestClient(app)
        r = c.post("/api/chat", json={"session_id": "t"})  # missing message
        assert r.status_code == 422


def test_chat_sync_500_on_exception():
    """Test 500 error when backend fails with an unexpected exception."""
    with override_chat_service(FakeFailClient()):
        c = TestClient(app)
        r = c.post("/api/chat", json={"message": "ping"})
        assert r.status_code == 500


def test_chat_sync_400_on_value_error():
    """Test 400 error when service raises ValueError (treated as validation)."""
    with override_chat_service(FakeValidationErrorClient()):
        c = TestClient(app)
        r = c.post("/api/chat", json={"message": "ping"})
        assert r.status_code == 400


def test_chat_sync_503_on_llm_unavailable():
    """Test 503 error when LLM client is unavailable (ConnectError)."""
    with override_chat_service(FakeUnavailableClient()):
        c = TestClient(app)
        r = c.post("/api/chat", json={"message": "ping"})
        assert r.status_code == 503


def test_chat_stream_get_200_sse_and_done_metrics():
    """Test SSE streaming with token and done events."""
    with override_chat_service(FakeOKClient()):
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
    """Test validation error when message param is missing."""
    with override_chat_service(FakeOKClient()):
        c = TestClient(app)
        r = c.get("/api/chat/stream")  # missing ?message
        assert r.status_code == 422


def test_chat_stream_get_backend_error_event_instead_of_500():
    """Test that backend errors are sent as SSE events, not HTTP 500."""
    with override_chat_service(FakeFailClient()):
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


def test_chat_stream_backend_error_payload_connect_error():
    """backend-error payload for ConnectError exposes llm_unavailable code."""
    payload = _read_backend_error_payload(
        fake_client=FakeUnavailableClient(),
        params={"message": "hello"},
    )

    # format_stream_error -> {"code": "llm_unavailable", "message": "LLM unavailable"}
    assert payload == {
        "code": "llm_unavailable",
        "message": "LLM unavailable",
    }


def test_chat_stream_backend_error_payload_timeout():
    """backend-error payload for TimeoutException also maps to llm_unavailable."""
    payload = _read_backend_error_payload(
        fake_client=FakeTimeoutClient(),
        params={"message": "hello"},
    )

    assert payload == {
        "code": "llm_unavailable",
        "message": "LLM unavailable",
    }


def test_chat_stream_backend_error_payload_validation_error():
    """backend-error payload for validation-like error exposes validation_error code."""
    payload = _read_backend_error_payload(
        fake_client=FakeValidationErrorClient(),
        params={"message": "hello"},
    )

    assert payload == {
        "code": "validation_error",
        "message": "Invalid: invalid",
    }


# ---- Memory tests (moved here) ------------------------------------------


class _FakeMemModel:
    """Fake model that returns message count for testing memory."""

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
def override_chat_service_with_fake_mem():
    """Override with a fake model that returns message count."""
    memory = SessionMemory(default_system_prompt="SYS")
    fake_llm_client = LLMClient(llm=_FakeMemModel(), system_prompt="SYS")
    service = ChatService(llm_client=fake_llm_client, memory=memory)

    app.dependency_overrides[get_chat_service] = lambda: service
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_chat_service, None)


def test_chat_memory_sync_len_increases_with_session():
    """Test that session memory accumulates messages."""
    with override_chat_service_with_fake_mem():
        c = TestClient(app)
        r1 = c.post("/api/chat", json={"message": "hi"})
        assert r1.status_code == 200
        sid = r1.json()["session_id"]
        assert sid

        r2 = c.post("/api/chat", json={"message": "help", "session_id": sid})
        assert r2.status_code == 200
        assert r2.json()["content"].startswith("LEN=")
        # Should have: system + user1 + assistant1 + user2 = 4 messages
        assert int(r2.json()["content"].split("=")[1]) >= 3


def test_chat_memory_sync_explicit_messages_override_server_memory():
    """Test that explicit messages override session memory."""
    with override_chat_service_with_fake_mem():
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
    """Test that streaming generates session and accumulates history."""
    with override_chat_service_with_fake_mem():
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
                    # Should have system + user message
                    assert int(s.rsplit("=", 1)[1]) >= 2
                    saw_len = True
            assert saw_len
            assert new_sid

        # Second request in same session
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
                    # Should have accumulated: system + user1 + assistant1 + user2
                    assert int(s.rsplit("=", 1)[1]) >= 3
                    saw_len2 = True
            assert saw_len2
