from __future__ import annotations

from typing import AsyncGenerator, List, Optional, Sequence

from langchain_ollama import ChatOllama
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    BaseMessage,
    AIMessage,
    AIMessageChunk,
)

from app.core.logging import get_logger

logger = get_logger("services.llm_client")

DEFAULT_SYSTEM_PROMPT = (
    # Keep this concise and safe. Do not force a specific language; mirror user's language.
    "You are a helpful, concise assistant. "
    "Always answer in the same language as the user's last message. "
    "Be accurate, avoid hallucinations, and ask for clarification when input is ambiguous."
)


class LLMClient:
    """A thin adapter around ChatOllama with a streaming API and a fixed system prompt."""

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        # Extra generation controls are passed via model_kwargs
        model_kwargs: Optional[dict] = None,
        llm: Optional[object] = None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        self.system_prompt = system_prompt

        if llm is not None:
            # For tests: inject a fake model that exposes .astream/.invoke
            self.llm = llm  # type: ignore[assignment]
            logger.info("LLMClient initialized with injected llm (test/dummy).")
            return

        kwargs = model_kwargs or {}
        # streaming=True ensures we can astream tokens
        self.llm = ChatOllama(
            base_url=base_url,
            model=model,
            temperature=temperature,
            streaming=True,
            # Many Ollama controls are supported via model_kwargs:
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

    @staticmethod
    def _to_messages(
        user_messages: Sequence[str],
        system_prompt: Optional[str],
    ) -> List[BaseMessage]:
        """Convert raw user strings into LangChain Message objects."""
        messages: List[BaseMessage] = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        for text in user_messages:
            messages.append(HumanMessage(content=text))
        return messages

    async def astream_chat(
        self,
        user_messages: Sequence[str] | Sequence[BaseMessage],
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Async generator yielding text chunks for streaming responses."""
        # Build messages list; if BaseMessage already provided, keep as-is.
        if user_messages and isinstance(user_messages[0], BaseMessage):  # type: ignore[index]
            messages: List[BaseMessage] = list(user_messages)  # type: ignore[assignment]
        else:
            messages = self._to_messages(
                user_messages=user_messages,  # type: ignore[arg-type]
                system_prompt=system_prompt or self.system_prompt,
            )

        logger.debug("astream_chat: messages=%d", len(messages))
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
        """Async convenience method returning the full response text."""
        if user_messages and isinstance(user_messages[0], BaseMessage):  # type: ignore[index]
            messages: List[BaseMessage] = list(user_messages)  # type: ignore[assignment]
        else:
            messages = self._to_messages(
                user_messages=user_messages,  # type: ignore[arg-type]
                system_prompt=system_prompt or self.system_prompt,
            )
        res = await self.llm.ainvoke(messages)  # use async to align with API layer
        return getattr(res, "content", str(res))

    # Sync version is used by some tests; keep it.
    def invoke(
        self,
        user_messages: Sequence[str] | Sequence[BaseMessage],
        system_prompt: Optional[str] = None,
    ) -> str:
        """Synchronous convenience method using the same message build path."""
        if user_messages and isinstance(user_messages[0], BaseMessage):  # type: ignore[index]
            messages: List[BaseMessage] = list(user_messages)  # type: ignore[assignment]
        else:
            messages = self._to_messages(
                user_messages=user_messages,  # type: ignore[arg-type]
                system_prompt=system_prompt or self.system_prompt,
            )
        res = self.llm.invoke(messages)
        return getattr(res, "content", str(res))
