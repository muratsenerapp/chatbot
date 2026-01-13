"""Session id utilities."""

from __future__ import annotations

from uuid import uuid4


def ensure_session_id(sid: str | None) -> str:
    """Return the given session id or generate a new UUID4 string.

    Args:
        sid: Existing session id, if any.

    Returns:
        A usable session id string (existing one or a new UUID4).
    """
    return sid or str(uuid4())
