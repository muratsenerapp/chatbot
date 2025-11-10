from __future__ import annotations
from typing import Optional
from uuid import uuid4


def ensure_session_id(sid: Optional[str]) -> str:
    """Return existing session id or fabricate a new uuid4."""
    return sid or str(uuid4())
