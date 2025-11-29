"""Metrics helpers and data structures for chat processing."""

from __future__ import annotations

from dataclasses import dataclass
import time

from langchain_core.messages import HumanMessage

from app.utils.token_counter import estimate_tokens_from_messages

INPUT_WARNING_THRESHOLD = 0.8
TOTAL_WARNING_THRESHOLD = 0.9


@dataclass
class ChatMetrics:
    """Metrics from chat processing.

    Attributes:
        input_tokens: Estimated number of input tokens.
        output_tokens: Estimated number of output tokens.
        total_tokens: Sum of input and output tokens.
        elapsed_ms: Processing time in milliseconds.
        is_near_limit: Whether total tokens approach context/prediction limits.
    """

    input_tokens: int
    output_tokens: int
    total_tokens: int
    elapsed_ms: float
    is_near_limit: bool


def calculate_chat_metrics(
    input_tokens: int,
    response_text: str,
    num_ctx: int,
    num_predict: int,
    start_time: float,
    total_warning_threshold: float = TOTAL_WARNING_THRESHOLD,
) -> ChatMetrics:
    """Compute latency and token usage metrics for a chat completion.

    This helper estimates the number of output tokens from the model response
    and derives aggregate metrics such as total tokens and whether the request
    is approaching the model's context and prediction limits.

    Args:
        input_tokens: Estimated number of tokens in the input prompt, including
            system, user and history messages that were sent to the model.
        response_text: Raw text returned by the model for this completion.
        num_ctx: Maximum context window of the model (e.g. `num_ctx` parameter
            passed to the underlying LLM).
        num_predict: Maximum number of tokens the model is allowed to generate
            for this completion.
        start_time: Monotonic timestamp (as returned by ``time.perf_counter()``)
            taken immediately before sending the request to the model. Used to
            compute the end-to-end latency.
        total_warning_threshold: Ratio in the range [0, 1] used to decide when
            the sum of input and output tokens should be considered "near the
            limit". The threshold is applied to ``num_ctx + num_predict``.

    Returns:
        ChatMetrics: Metrics object containing input/output token counts,
        total token usage, elapsed time in milliseconds and a flag indicating
        whether the request is close to the configured token limit.
    """
    elapsed = (time.perf_counter() - start_time) * 1000
    output_tokens = estimate_tokens_from_messages([HumanMessage(content=response_text)])
    total_tokens = input_tokens + output_tokens
    is_near_limit = total_tokens > int(
        total_warning_threshold * (num_ctx + num_predict)
    )

    return ChatMetrics(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        elapsed_ms=elapsed,
        is_near_limit=is_near_limit,
    )
