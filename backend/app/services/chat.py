"""Chat service providing message processing, streaming, and conversation management.

Coordinates LLM invocation, session memory, token counting, and metrics collection
for both single-shot and streaming chat interactions.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import AsyncGenerator

from langchain_core.messages import BaseMessage, HumanMessage

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.llm import LLMClient
from app.services.memory import SessionMemory
from app.services.metrics import (
    INPUT_WARNING_THRESHOLD,
    ChatMetrics,
    calculate_chat_metrics,
)
from app.utils.token_counter import estimate_tokens_from_messages

logger = get_logger(__name__)


@dataclass
class StreamChunk:
    """Single chunk from streaming response.

    Attributes:
        token: Text content of the chunk.
        char_count: Cumulative character count up to this chunk.
    """

    token: str
    char_count: int


@dataclass
class StreamComplete:
    """Stream completion metadata.

    Attributes:
        session_id: Session identifier for the completed stream.
        total_chars: Total character count in the complete response.
        metrics: Processing metrics including token counts and timing.
    """

    session_id: str
    total_chars: int
    metrics: ChatMetrics


class ChatService:
    """Handle chat business logic.

    Responsibilities:
    - Process user messages (streaming and non-streaming)
    - Manage conversation context
    - Calculate and track metrics
    - Validate context windows
    """

    def __init__(
        self,
        llm_client: LLMClient,
        memory: SessionMemory,
    ):
        """Initialize the chat service with LLM client and memory.

        Args:
            llm_client: Client for LLM invocation and streaming.
            memory: Session-scoped message storage.
        """
        self.llm_client = llm_client
        self.memory = memory

    async def process_message(
        self,
        message: str,
        session_id: str,
        explicit_messages: list[BaseMessage] | None = None,
    ) -> tuple[str, ChatMetrics]:
        """Process a chat message and return a full response with metrics.

        Args:
            message: User input text.
            session_id: Session identifier for conversation context.
            explicit_messages: Optional pre-built message list to override session memory.

        Returns:
            Tuple of (assistant response text, processing metrics).
        """
        start = time.perf_counter()

        model_messages = await self._prepare_messages(
            message, session_id, explicit_messages
        )

        input_tokens, num_ctx, num_predict = self._calculate_and_validate_input(
            model_messages, session_id
        )

        response = await self.llm_client.ainvoke(model_messages)

        await self._update_memory_if_needed(
            session_id, message, response, explicit_messages
        )

        metrics = calculate_chat_metrics(
            input_tokens=input_tokens,
            response_text=response,
            num_ctx=num_ctx,
            num_predict=num_predict,
            start_time=start,
        )

        logger.info(
            "Chat processed: session=%s, input=%d, output=%d, elapsed=%.1fms",
            session_id,
            input_tokens,
            metrics.output_tokens,
            metrics.elapsed_ms,
        )

        return response, metrics

    async def process_message_stream(
        self,
        message: str,
        session_id: str,
        explicit_messages: list[BaseMessage] | None = None,
    ) -> AsyncGenerator[StreamChunk | StreamComplete, None]:
        """Process a chat message and stream response tokens.

        Args:
            message: User input text.
            session_id: Session identifier for conversation context.
            explicit_messages: Optional pre-built message list to override session memory.

        Yields:
            StreamChunk: For each token with cumulative character count.
            StreamComplete: Final metadata when done including metrics.
        """
        start = time.perf_counter()

        model_messages = await self._prepare_messages(
            message, session_id, explicit_messages
        )

        input_tokens, num_ctx, num_predict = self._calculate_and_validate_input(
            model_messages, session_id
        )

        char_count = 0
        assistant_text_parts: list[str] = []

        async for chunk in self.llm_client.astream_chat(model_messages):
            if not chunk:
                continue

            char_count += len(chunk)
            assistant_text_parts.append(chunk)

            yield StreamChunk(token=chunk, char_count=char_count)

        full_text = "".join(assistant_text_parts)

        await self._update_memory_if_needed(
            session_id, message, full_text, explicit_messages
        )

        metrics = calculate_chat_metrics(
            input_tokens=input_tokens,
            response_text=full_text,
            num_ctx=num_ctx,
            num_predict=num_predict,
            start_time=start,
        )

        logger.info(
            "Stream completed: session=%s, input=%d, output=%d, elapsed=%.1fms",
            session_id,
            input_tokens,
            metrics.output_tokens,
            metrics.elapsed_ms,
        )

        if metrics.is_near_limit:
            logger.warning(
                "Total tokens near limit: %d (session=%s)",
                metrics.total_tokens,
                session_id,
            )

        yield StreamComplete(
            session_id=session_id, total_chars=char_count, metrics=metrics
        )

    async def _prepare_messages(
        self,
        message: str,
        session_id: str,
        explicit_messages: Sequence[BaseMessage] | None = None,
    ) -> list[BaseMessage]:
        """Prepare a mutable message list for LLM invocation.

        Either returns a list built from explicit messages or constructs one
        from the session history plus the current user message.

        Args:
            message: Current user message to append.
            session_id: Session identifier used for history lookup.
            explicit_messages: Optional sequence of pre-built messages to use
                instead of the session history. If provided, the returned list
                is a copy of this sequence.

        Returns:
            A new list of BaseMessage objects for LLM invocation.
        """
        if explicit_messages is not None:
            return list(explicit_messages)

        sys_prompt = self.llm_client.system_prompt
        await self.memory.ensure_session(session_id, sys_prompt)
        history = await self.memory.get_messages(session_id)

        return [*history, HumanMessage(content=message)]

    def _calculate_and_validate_input(
        self,
        model_messages: list[BaseMessage],
        session_id: str,
    ) -> tuple[int, int, int]:
        """Calculate input tokens and validate against a context window.

        Returns:
            tuple: (input_tokens, num_ctx, num_predict)
        """
        input_tokens = estimate_tokens_from_messages(model_messages)
        num_ctx, num_predict = self._get_context_settings()

        if input_tokens > int(INPUT_WARNING_THRESHOLD * num_ctx):
            logger.warning(
                "Input near limit: %d/%d tokens (session=%s)",
                input_tokens,
                num_ctx,
                session_id,
            )

        return input_tokens, num_ctx, num_predict

    async def _update_memory_if_needed(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        explicit_messages: list[BaseMessage] | None,
    ) -> None:
        """Update session memory if not using explicit messages.

        Args:
            session_id: Session identifier to update.
            user_message: User message content to store.
            assistant_response: Assistant response content to store.
            explicit_messages: If provided, memory update is skipped.
        """
        if not explicit_messages:
            await self.memory.append_turn(
                session_id,
                user_message,
                assistant_response,
                system_prompt=self.llm_client.system_prompt,
            )

    def _get_context_settings(self) -> tuple[int, int]:
        """Get context window settings from the LLM client.

        Falls back to centralized config values (OLLAMA_NUM_CTX, OLLAMA_NUM_PREDICT)
        if the LLM client doesn't have explicit settings.
        """
        settings = get_settings()
        return self.llm_client.get_context_limits(
            default_ctx=settings.OLLAMA_NUM_CTX,
            default_num_predict=settings.OLLAMA_NUM_PREDICT,
        )
