from dataclasses import dataclass
from typing import Optional, AsyncGenerator
import time

from langchain_core.messages import BaseMessage, HumanMessage

from app.services.llm import LLMClient
from app.services.memory import SessionMemory
from app.utils.token_counter import estimate_tokens_from_messages
from app.core.logging import get_logger

INPUT_WARNING_THRESHOLD = 0.8
TOTAL_WARNING_THRESHOLD = 0.9
DEFAULT_CONTEXT_WINDOW = 4096
DEFAULT_MAX_PREDICT = 512

logger = get_logger(__name__)


@dataclass
class ChatMetrics:
    """Metrics from chat processing."""

    input_tokens: int
    output_tokens: int
    total_tokens: int
    elapsed_ms: float
    is_near_limit: bool


@dataclass
class StreamChunk:
    """Single chunk from streaming response."""

    token: str
    char_count: int


@dataclass
class StreamComplete:
    """Stream completion metadata."""

    session_id: str
    total_chars: int
    metrics: ChatMetrics


class ChatService:
    """
    Handle chat business logic.

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
        self.llm_client = llm_client
        self.memory = memory

    async def process_message(
        self,
        message: str,
        session_id: str,
        explicit_messages: Optional[list[BaseMessage]] = None,
    ) -> tuple[str, ChatMetrics]:
        """Process a chat message and return a full response with metrics."""
        start = time.perf_counter()

        # Prepare messages - EXTRACTED
        model_messages = self._prepare_messages(message, session_id, explicit_messages)

        # Calculate and validate - EXTRACTED
        input_tokens, num_ctx, num_predict = self._calculate_and_validate_input(
            model_messages, session_id
        )

        # Invoke LLM
        response = await self.llm_client.ainvoke(model_messages)

        # Update memory - EXTRACTED
        self._update_memory_if_needed(session_id, message, response, explicit_messages)

        # Calculate metrics - EXTRACTED
        metrics = self._calculate_metrics(
            input_tokens, response, num_ctx, num_predict, start
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
        """
        Process a chat message and stream response tokens.

        Yields:
            StreamChunk: For each token
            StreamComplete: Final metadata when done
        """
        start = time.perf_counter()

        # Prepare messages - REUSED
        model_messages = self._prepare_messages(message, session_id, explicit_messages)

        # Calculate and validate - REUSED
        input_tokens, num_ctx, num_predict = self._calculate_and_validate_input(
            model_messages, session_id
        )

        # Stream from LLM
        char_count = 0
        assistant_text_parts: list[str] = []

        async for chunk in self.llm_client.astream_chat(model_messages):
            if not chunk:
                continue

            char_count += len(chunk)
            assistant_text_parts.append(chunk)

            # Yield token chunk
            yield StreamChunk(token=chunk, char_count=char_count)

        # Complete response
        full_text = "".join(assistant_text_parts)

        # Update memory - REUSED
        self._update_memory_if_needed(session_id, message, full_text, explicit_messages)

        # Calculate metrics - REUSED
        metrics = self._calculate_metrics(
            input_tokens, full_text, num_ctx, num_predict, start
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

        # Yield completion metadata
        yield StreamComplete(
            session_id=session_id, total_chars=char_count, metrics=metrics
        )

    def _prepare_messages(
        self,
        message: str,
        session_id: str,
        explicit_messages: Optional[list[BaseMessage]],
    ) -> list[BaseMessage]:
        """
        Prepare messages for LLM invocation.

        Either uses explicit messages or builds from session history.
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
        """
        Calculate input tokens and validate against a context window.

        Returns:
            tuple: (input_tokens, num_ctx, num_predict)
        """
        input_tokens = estimate_tokens_from_messages(model_messages)
        num_ctx, num_predict = self._get_context_settings()

        # Log warning if near the context limit
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
        """Update session memory if not using explicit messages."""
        if not explicit_messages:
            self.memory.append_turn(
                session_id,
                user_message,
                assistant_response,
                system_prompt=self.llm_client.system_prompt,
            )

    def _get_context_settings(self) -> tuple[int, int]:
        """Get context window settings from the LLM client."""
        try:
            model_kwargs = getattr(self.llm_client.llm, "model_kwargs", {})
            num_ctx = model_kwargs.get("num_ctx", DEFAULT_CONTEXT_WINDOW)
            num_predict = model_kwargs.get("num_predict", DEFAULT_MAX_PREDICT)
        except AttributeError:
            # LLM client doesn't have expected attributes
            num_ctx, num_predict = DEFAULT_CONTEXT_WINDOW, DEFAULT_MAX_PREDICT

        return num_ctx, num_predict

    @staticmethod
    def _calculate_metrics(
        input_tokens: int,
        response_text: str,
        num_ctx: int,
        num_predict: int,
        start_time: float,
    ) -> ChatMetrics:
        """Calculate chat metrics from processing."""
        elapsed = (time.perf_counter() - start_time) * 1000
        output_tokens = estimate_tokens_from_messages(
            [HumanMessage(content=response_text)]
        )
        total_tokens = input_tokens + output_tokens
        is_near_limit = total_tokens > int(
            TOTAL_WARNING_THRESHOLD * (num_ctx + num_predict)
        )

        return ChatMetrics(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            elapsed_ms=elapsed,
            is_near_limit=is_near_limit,
        )
