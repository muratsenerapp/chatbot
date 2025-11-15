import pytest
from langchain_core.messages import AIMessageChunk
from app.services.llm import LLMClient


class FakeStreamModel:
    async def astream(self, _messages):
        for ch in ["An", "ka", "ra"]:
            yield AIMessageChunk(content=ch)

    def invoke(self, _messages):
        class R:
            content = "Ankara"

        return R()


@pytest.mark.asyncio
async def test_stream_tokens_with_fake_model():
    client = LLMClient(llm=FakeStreamModel())
    parts = []
    async for t in client.astream_chat(["Türkiye'nin başkenti?"]):
        parts.append(t)
    assert "".join(parts) == "Ankara"


def test_invoke_sync_with_fake_model():
    client = LLMClient(llm=FakeStreamModel())
    assert client.invoke(["Türkiye'nin başkenti?"]) == "Ankara"
