# backend/app/services/llm_client.py
from __future__ import annotations
from typing import AsyncGenerator, Optional, Sequence, List

from langchain_ollama import ChatOllama
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    BaseMessage,
    AIMessage,
    AIMessageChunk,
)

DEFAULT_SYSTEM_PROMPT = (
    "Respond in **Turkish**. Keep answers short, clear, and accurate; "
    "avoid unnecessary details and say if you're uncertain."
)


class LLMClient:
    """Thin wrapper around LangChain ChatOllama."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:7b-instruct-q4",
        temperature: float = 0.2,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        llm: Optional[ChatOllama] = None,
    ) -> None:
        self.system_prompt = system_prompt
        self.llm = llm or ChatOllama(
            base_url=base_url,
            model=model,
            temperature=temperature,
            streaming=True,
        )

    @staticmethod
    def _to_messages(
        user_messages: Sequence[str],
        system_prompt: Optional[str],
    ) -> List[BaseMessage]:
        messages: List[BaseMessage] = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        for m in user_messages:
            messages.append(HumanMessage(content=m))
        return messages

    async def astream_chat(
        self,
        user_messages: Sequence[str] | Sequence[BaseMessage],
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        if not user_messages:
            return

        if isinstance(user_messages[0], BaseMessage):  # type: ignore[index]
            messages: List[BaseMessage] = list(user_messages)
        else:
            messages = self._to_messages(
                user_messages=user_messages,  # type: ignore[arg-type]
                system_prompt=system_prompt or self.system_prompt,
            )

        async for chunk in self.llm.astream(messages):
            if isinstance(chunk, AIMessageChunk):
                if chunk.content:
                    yield str(chunk.content)
            elif isinstance(chunk, AIMessage):
                yield str(chunk.content)
            else:
                text = getattr(chunk, "content", None)
                if text:
                    yield str(text)

    async def ainvoke(
        self,
        user_messages: Sequence[str] | Sequence[BaseMessage],
        system_prompt: Optional[str] = None,
    ) -> str:
        parts: list[str] = []
        async for t in self.astream_chat(user_messages, system_prompt=system_prompt):
            parts.append(t)
        return "".join(parts)

    def invoke(
        self,
        user_messages: Sequence[str] | Sequence[BaseMessage],
        system_prompt: Optional[str] = None,
    ) -> str:
        if user_messages and isinstance(user_messages[0], BaseMessage):  # type: ignore[index]
            messages: List[BaseMessage] = list(user_messages)  # type: ignore[assignment]
        else:
            messages = self._to_messages(
                user_messages=user_messages,  # type: ignore[arg-type]
                system_prompt=system_prompt or self.system_prompt,
            )
        res = self.llm.invoke(messages)
        return getattr(res, "content", str(res))
