"""Thin wrapper around LangChain's ChatOllama providing streaming and convenience helpers."""

from __future__ import annotations

from typing import Any, AsyncGenerator, AsyncIterator, Mapping, Protocol, Sequence

from langchain_core.messages import BaseMessage, AIMessage, AIMessageChunk
from langchain_ollama import ChatOllama

from app.core.logging import get_logger
from app.utils.message_converter import (
    to_langchain_messages,
    is_langchain_message_list,
)

logger = get_logger(__name__)


DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful, concise assistant. "
    "Be accurate, avoid hallucinations, and ask for clarification when input is ambiguous."
)


class SupportsChat(Protocol):
    """Minimal protocol that the underlying LLM client must satisfy."""

    async def astream(
        self, messages: Sequence[BaseMessage], **kwargs: Any
    ) -> AsyncIterator[AIMessageChunk]: ...

    async def ainvoke(
        self, messages: Sequence[BaseMessage], **kwargs: Any
    ) -> AIMessage: ...

    def invoke(self, messages: Sequence[BaseMessage], **kwargs: Any) -> AIMessage: ...


class LLMClient:
    """
    A thin adapter around ChatOllama with a streaming API and a fixed system prompt.

    Provides three invocation methods:
      - astream_chat: async streaming (token by token)
      - ainvoke: async full response
      - invoke: sync full response
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        model: str | None = None,
        temperature: float = 0.2,
        model_kwargs: Mapping[str, Any] | None = None,
        llm: SupportsChat | None = None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        """
        Initialize a ChatOllama-backed client with a consistent system prompt.

        If an ``llm`` is provided, it is used directly (handy for tests).
        Otherwise a streaming-capable ChatOllama client is constructed.
        """
        self.system_prompt = system_prompt

        if llm is not None:
            self.llm: SupportsChat = llm
            logger.info("LLMClient initialized with injected llm.")
            return

        kwargs: dict[str, Any] = dict(model_kwargs or {})
        self.llm = ChatOllama(
            base_url=base_url,
            model=model,
            temperature=temperature,
            streaming=True,
            model_kwargs=kwargs,
        )
        logger.info(
            "LLMClient initialized base_url=%s model=%s temp=%s ctx=%s predict=%s",
            base_url,
            model,
            temperature,
            kwargs.get("num_ctx"),
            kwargs.get("num_predict"),
        )

    def _prepare_messages(
        self,
        user_messages: Sequence[str] | Sequence[BaseMessage],
        system_prompt: str | None,
    ) -> list[BaseMessage]:
        """Normalize user input into a list of LangChain messages."""
        if is_langchain_message_list(user_messages):
            messages = list(user_messages)
        else:
            messages = to_langchain_messages(
                user_messages,
                system_prompt or self.system_prompt,
            )

        logger.debug("prepared %d messages", len(messages))
        return messages

    @staticmethod
    def _to_text(obj: object) -> str | None:
        """Best-effort extraction of textual content from model outputs."""
        if isinstance(obj, (AIMessageChunk, AIMessage)):
            if obj.content:
                return str(obj.content)
            return None

        text = getattr(obj, "content", None)
        if text:
            return str(text)
        return None

    async def astream_chat(
        self,
        user_messages: Sequence[str] | Sequence[BaseMessage],
        system_prompt: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream response text chunks as they arrive from the model.

        Yields plain text segments in arrival order.
        """
        messages = self._prepare_messages(user_messages, system_prompt)

        async for chunk in self.llm.astream(messages):
            text = self._to_text(chunk)
            if text:
                yield text

    async def ainvoke(
        self,
        user_messages: Sequence[str] | Sequence[BaseMessage],
        system_prompt: str | None = None,
    ) -> str:
        """Return the full assistant response as a single string (async)."""
        messages = self._prepare_messages(user_messages, system_prompt)
        res = await self.llm.ainvoke(messages)
        return self._to_text(res) or str(res)

    def invoke(
        self,
        user_messages: Sequence[str] | Sequence[BaseMessage],
        system_prompt: str | None = None,
    ) -> str:
        """Return the full assistant response as a single string (sync)."""
        messages = self._prepare_messages(user_messages, system_prompt)
        res = self.llm.invoke(messages)
        return self._to_text(res) or str(res)
