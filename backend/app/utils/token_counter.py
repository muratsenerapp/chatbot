from __future__ import annotations

from typing import Iterable

# We avoid extra heavy deps. This is a heuristic:
# For Latin-script languages (incl. Turkish/English), ~4 chars per token is a
# reasonable approximation for monitoring/logging purposes.
CHAR_PER_TOKEN = 4


def estimate_tokens_from_text(text: str) -> int:
    """Return a rough token estimate for a single text."""
    if not text:
        return 0
    return max(1, len(text) // CHAR_PER_TOKEN)


def estimate_tokens_from_iter(texts: Iterable[str]) -> int:
    """Return a rough token estimate for concatenation of many texts."""
    total = 0
    for t in texts:
        total += estimate_tokens_from_text(t)
    return total
