"""Thin wrapper around LangChain's ChatOllama providing streaming and convenience helpers."""

from __future__ import annotations

from typing import AsyncGenerator, Optional, Sequence

from langchain_core.messages import (
    BaseMessage,
    AIMessage,
    AIMessageChunk,
)
from langchain_ollama import ChatOllama

from app.core.logging import get_logger
from app.utils.message_converter import to_langchain_messages, is_langchain_message_list

logger = get_logger("services.llm_client")

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful, concise assistant. "
    "Be accurate, avoid hallucinations, and ask for clarification when input is ambiguous."
)


class LLMClient:
    """
    A thin adapter around ChatOllama with a streaming API and a fixed system prompt.

    Provides three invocation methods:
    - astream_chat: Async streaming (token by token)
    - ainvoke: Async full response
    - invoke: Sync full response
    """

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        model_kwargs: Optional[dict] = None,
        llm: Optional[object] = None,
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
            # Accept a pre-initialized compatible client (mock or custom backend).
            self.llm = llm
            logger.info("LLMClient initialized with injected llm.")
            return

        kwargs = model_kwargs or {}
        # streaming=True ensures we can astream tokens
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

    async def astream_chat(
        self,
        user_messages: Sequence[str] | Sequence[BaseMessage],
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream response text chunks as they arrive from the model.

        Args:
            user_messages: Either raw user turns as strings or a prebuilt list of
                LangChain messages. When strings are provided, a system message is
                prepended if available.
            system_prompt: Per-call override for the default system prompt. If None,
                `self.system_prompt` is used.

        Yields:
            str: Pieces of the assistant's textual response in arrival order.

        Example:
            async for token in client.astream_chat(["What's 2+2?"]):
                print (token, end="", flush=True)
            The answer is 4.
        """
        # Prepare messages
        if is_langchain_message_list(user_messages):
            messages = list(user_messages)
        else:
            messages = to_langchain_messages(
                user_messages, system_prompt or self.system_prompt
            )

        logger.debug("astream_chat: messages=%d", len(messages))

        # Stream from LLM
        async for chunk in self.llm.astream(messages):
            if isinstance(chunk, AIMessageChunk):
                if chunk.content:
                    yield str(chunk.content)
            elif isinstance(chunk, AIMessage):
                yield str(chunk.content)
            else:
                # Fallback for other chunk types
                text = getattr(chunk, "content", None)
                if text:
                    yield str(text)

    async def ainvoke(
        self,
        user_messages: Sequence[str] | Sequence[BaseMessage],
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Return the full response text asynchronously.

        Args:
            user_messages: Raw user turns as strings or a prebuilt list of LangChain
                messages; when strings are provided, a system message is prepended if available.
            system_prompt: Per-call override for the default system prompt.

        Returns:
            Full assistant response as a single string.

        Example:
             response = await client.ainvoke(["What's the capital of France?"])
             print(response)
            The capital of France is Paris.
        """
        # Prepare messages
        if is_langchain_message_list(user_messages):
            messages = list(user_messages)
        else:
            messages = to_langchain_messages(
                user_messages, system_prompt or self.system_prompt
            )

        logger.debug("ainvoke: messages=%d", len(messages))

        # Invoke LLM
        res = await self.llm.ainvoke(messages)
        return getattr(res, "content", str(res))

    def invoke(
        self,
        user_messages: Sequence[str] | Sequence[BaseMessage],
        system_prompt: Optional[str] = None,
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
            response = client.invoke(["Tell me a joke"])
            print(response)
            Why did the chicken cross the road? To get to the other side!
        """
        # Prepare messages
        if is_langchain_message_list(user_messages):
            messages = list(user_messages)
        else:
            messages = to_langchain_messages(
                user_messages, system_prompt or self.system_prompt
            )

        logger.debug("invoke: messages=%d", len(messages))

        # Invoke LLM
        res = self.llm.invoke(messages)
        return getattr(res, "content", str(res))
