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

        Uses an injected ``llm`` when provided (useful for tests); otherwise constructs a
        streaming-capable network client. Additional provider options can be forwarded via
        ``model_kwargs``.

        Args:
            base_url: Base URL of the Ollama server (e.g., ``http://localhost:11434``).
            model: Name/tag of the model to use on the Ollama server.
            temperature: Sampling temperature controlling randomness of outputs.
            model_kwargs: Provider-specific generation options passed to Ollama
                (for example, ``num_ctx``, ``num_predict``).
            llm: Pre-initialized model object exposing ``astream``/``ainvoke``/``invoke`` to
                bypass network setup; typically injected in tests.
            system_prompt: Default system prompt prepended to conversations when not overridden.
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
        """Stream response text chunks as they arrive from the model.

        Args:
            user_messages: Either raw user turns as strings or a prebuilt list...
            system_prompt: Per-call override for the default system prompt.

        Yields:
            str: Pieces of the assistant's textual response in arrival order.

        Example:
            client = LLMClient(base_url="http://localhost:11434", model="qwen2.5:7b-instruct")

            async for token in client.astream_chat(["What's 2+2?"]):
                print(token, end="", flush=True)

            # Output: The answer is 4.
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
        """Return the full response text asynchronously.

        Args:
            user_messages: Raw user turns as strings or a prebuilt list of LangChain
                messages; when strings are provided, a system message is prepended if available.
            system_prompt: Per-call override for the default system prompt.

        Returns:
            Full assistant response as a single string.

        Example:
            client = LLMClient(base_url="http://localhost:11434", model="qwen2.5:7b-instruct")

            response = await client.ainvoke(["What's the capital of France?"])
            print(response)

            # Output: The capital of France is Paris.
        """
        messages = self._prepare_messages(user_messages, system_prompt)
        res = await self.llm.ainvoke(messages)
        return self._to_text(res) or str(res)

    def invoke(
        self,
        user_messages: Sequence[str] | Sequence[BaseMessage],
        system_prompt: str | None = None,
    ) -> str:
        """
        Return the full response text synchronously.

        Args:
            user_messages: Raw user turns as strings or a prebuilt list of LangChain
                messages; when strings are provided, a system message is prepended if available.
            system_prompt: Per-call override for the default system prompt.

        Returns:
            Full assistant response as a single string.

        Example:
            client = LLMClient(base_url="http://localhost:11434", model="qwen2.5:7b-instruct")

            response = client.invoke(["Tell me a joke"])
            print(response)

            # Output: Why did the chicken cross the road? To get to the other side!
        """
        messages = self._prepare_messages(user_messages, system_prompt)
        res = self.llm.invoke(messages)
        return self._to_text(res) or str(res)
