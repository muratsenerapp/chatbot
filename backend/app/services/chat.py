"""Chat service providing message processing, streaming, and conversation management.

Coordinates LLM invocation, session memory, token counting, and metrics collection
for both single-shot and streaming chat interactions.
"""

from dataclasses import dataclass
from typing import Optional, AsyncGenerator
import time

from langchain_core.messages import BaseMessage, HumanMessage

from app.services.llm import LLMClient
from app.services.memory import SessionMemory
from app.services.metrics import (
    ChatMetrics,
    INPUT_WARNING_THRESHOLD,
    calculate_chat_metrics,
)
from app.utils.token_counter import estimate_tokens_from_messages
from app.core.logging import get_logger


DEFAULT_CONTEXT_WINDOW = 4096
DEFAULT_MAX_PREDICT = 512

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
        explicit_messages: Optional[list[BaseMessage]] = None,
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

        model_messages = self._prepare_messages(message, session_id, explicit_messages)

        input_tokens, num_ctx, num_predict = self._calculate_and_validate_input(
            model_messages, session_id
        )

        response = await self.llm_client.ainvoke(model_messages)

        self._update_memory_if_needed(session_id, message, response, explicit_messages)

        metrics = calculate_chat_metrics(
            input_tokens=input_tokens,
            response_text=response,
            num_ctx=num_ctx,
            num_predict=num_predict,
            start_time=start,
        )

        logger.info(
            f"Chat processed: session={session_id}, "
            f"input={input_tokens}, output={metrics.output_tokens}, "
            f"elapsed={metrics.elapsed_ms:.1f}ms"
        )

        return response, metrics

    async def process_message_stream(
        self,
        message: str,
        session_id: str,
        explicit_messages: Optional[list[BaseMessage]] = None,
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

        model_messages = self._prepare_messages(message, session_id, explicit_messages)

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

        self._update_memory_if_needed(session_id, message, full_text, explicit_messages)

        metrics = calculate_chat_metrics(
            input_tokens=input_tokens,
            response_text=full_text,
            num_ctx=num_ctx,
            num_predict=num_predict,
            start_time=start,
        )

        logger.info(
            f"Stream completed: session={session_id}, "
            f"input={input_tokens}, output={metrics.output_tokens}, "
            f"elapsed={metrics.elapsed_ms:.1f}ms"
        )

        if metrics.is_near_limit:
            logger.warning(
                f"Total tokens near limit: {metrics.total_tokens} (session={session_id})"
            )

        yield StreamComplete(
            session_id=session_id, total_chars=char_count, metrics=metrics
        )

    def _prepare_messages(
        self,
        message: str,
        session_id: str,
        explicit_messages: Optional[list[BaseMessage]],
    ) -> list[BaseMessage]:
        """Prepare messages for LLM invocation.

        Either uses explicit messages or builds from session history.

        Args:
            message: Current user message to append.
            session_id: Session identifier for history lookup.
            explicit_messages: Optional pre-built messages to use instead of history.

        Returns:
            List of BaseMessage objects for LLM invocation.
        """
        if explicit_messages:
            return explicit_messages

        sys_prompt = self.llm_client.system_prompt
        self.memory.ensure_session(session_id, sys_prompt)
        history = self.memory.get_messages(session_id)
        return history + [HumanMessage(content=message)]

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
                f"Input near limit: {input_tokens}/{num_ctx} tokens (session={session_id})"
            )

        return input_tokens, num_ctx, num_predict

    def _update_memory_if_needed(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        explicit_messages: Optional[list[BaseMessage]],
    ) -> None:
        """Update session memory if not using explicit messages.

        Args:
            session_id: Session identifier to update.
            user_message: User message content to store.
            assistant_response: Assistant response content to store.
            explicit_messages: If provided, memory update is skipped.
        """
        if not explicit_messages:
            self.memory.append_turn(
                session_id,
                user_message,
                assistant_response,
                system_prompt=self.llm_client.system_prompt,
            )

    def _get_context_settings(self) -> tuple[int, int]:
        """Get context window settings from the LLM client."""
        return self.llm_client.get_context_limits(
            default_ctx=DEFAULT_CONTEXT_WINDOW,
            default_num_predict=DEFAULT_MAX_PREDICT,
        )
