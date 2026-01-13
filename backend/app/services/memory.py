"""Session-scoped in-memory chat history utilities.

Provides a simple per-session message buffer for chat conversations.
Not persisted but thread-safe using asyncio.Lock.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage


class SessionMemory:
    """In-memory session-scoped chat history.

    Stores a list of LangChain messages per `session_id`. This is a
    process-local helper for simple prototypes and testing; it does not persist
    data but is thread-safe using asyncio.Lock.
    """

    def __init__(self, default_system_prompt: str | None = None) -> None:
        """Initialize the store with an optional default system prompt.

        Args:
            default_system_prompt: System prompt to seed new sessions when a
                per-call prompt is not provided.
        """
        self._default_system_prompt = default_system_prompt
        self._store: dict[str, list[BaseMessage]] = {}
        self._lock = asyncio.Lock()

    async def ensure_session(
        self, session_id: str, system_prompt: str | None = None
    ) -> None:
        """Ensure a session buffer exists, optionally seeding a SystemMessage.

        Idempotent: if the session already exists, nothing changes.

        Args:
            session_id: Unique session key.
            system_prompt: System prompt used only when creating the session; if
                omitted, falls back to the `default_system_prompt`.
        """
        async with self._lock:
            if session_id not in self._store:
                sp = system_prompt or self._default_system_prompt
                self._store[session_id] = [SystemMessage(content=sp)] if sp else []

    async def get_messages(self, session_id: str) -> Sequence[BaseMessage]:
        """Return an immutable snapshot of the session messages.

        The returned tuple prevents external mutation of the internal message list.
        Returns an empty tuple if the session does not exist.

        Args:
            session_id: Session key to read.

        Returns:
            Immutable sequence (tuple) of messages for the given session.
        """
        async with self._lock:
            return tuple(self._store.get(session_id, ()))

    async def append_user(
        self, session_id: str, content: str, *, system_prompt: str | None = None
    ) -> None:
        """Append a user turn (HumanMessage), creating the session if needed.

        Args:
            session_id: Session key to write.
            content: User message content.
            system_prompt: Optional seed prompt if the session is being created.
        """
        async with self._lock:
            if session_id not in self._store:
                sp = system_prompt or self._default_system_prompt
                self._store[session_id] = [SystemMessage(content=sp)] if sp else []
            self._store[session_id].append(HumanMessage(content=content))

    async def append_assistant(
        self, session_id: str, content: str, *, system_prompt: str | None = None
    ) -> None:
        """Append an assistant turn (AIMessage), creating the session if needed.

        Args:
            session_id: Session key to write.
            content: Assistant message content.
            system_prompt: Optional seed prompt if the session is being created.
        """
        async with self._lock:
            if session_id not in self._store:
                sp = system_prompt or self._default_system_prompt
                self._store[session_id] = [SystemMessage(content=sp)] if sp else []
            self._store[session_id].append(AIMessage(content=content))

    async def append_turn(
        self,
        session_id: str,
        user_content: str,
        assistant_content: str,
        *,
        system_prompt: str | None = None,
    ) -> None:
        """Append a full user→assistant exchange atomically.

        Ensures the session exists (seeding a system prompt if needed), then
        appends the two messages in order.

        Args:
            session_id: Session key to write.
            user_content: User message text.
            assistant_content: Assistant reply text.
            system_prompt: Optional seed prompt if the session is being created.
        """
        async with self._lock:
            if session_id not in self._store:
                sp = system_prompt or self._default_system_prompt
                self._store[session_id] = [SystemMessage(content=sp)] if sp else []
            self._store[session_id].extend(
                [
                    HumanMessage(content=user_content),
                    AIMessage(content=assistant_content),
                ]
            )

    async def clear(self, session_id: str) -> None:
        """Remove all messages for a session; no error if it does not exist.

        Args:
            session_id: Session key to delete.
        """
        async with self._lock:
            self._store.pop(session_id, None)
