"""Session-scoped in-memory chat history utilities.

Provides a simple per-session message buffer for chat conversations.
Not persisted and not multiprocess/thread safe by design.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Dict, List, Optional

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage


class SessionMemory:
    """In-memory session-scoped chat history.

    Stores a list of LangChain messages per `session_id`. This is a
    process-local helper for simple prototypes and testing; it does not persist
    data and is not multiprocess/thread safe.
    """

    def __init__(self, default_system_prompt: Optional[str] = None) -> None:
        """Initialize the store with an optional default system prompt.

        Args:
            default_system_prompt: System prompt to seed new sessions when a
                per-call prompt is not provided.
        """
        self._default_system_prompt = default_system_prompt
        self._store: Dict[str, List[BaseMessage]] = {}

    def ensure_session(
        self, session_id: str, system_prompt: Optional[str] = None
    ) -> None:
        """Ensure a session buffer exists, optionally seeding a SystemMessage.

        Idempotent: if the session already exists, nothing changes.

        Args:
            session_id: Unique session key.
            system_prompt: System prompt used only when creating the session; if
                omitted, falls back to the `default_system_prompt`.
        """
        if session_id not in self._store:
            sp = system_prompt or self._default_system_prompt
            self._store[session_id] = [SystemMessage(content=sp)] if sp else []

    def get_messages(self, session_id: str) -> Sequence[BaseMessage]:
        """Return an immutable snapshot of the session messages.

        The returned tuple prevents external mutation of the internal message list.
        Returns an empty tuple if the session does not exist.

        Args:
            session_id: Session key to read.

        Returns:
            Immutable sequence (tuple) of messages for the given session.
        """
        return tuple(self._store.get(session_id, ()))

    def append_user(
        self, session_id: str, content: str, *, system_prompt: Optional[str] = None
    ) -> None:
        """Append a user turn (HumanMessage), creating the session if needed.

        Args:
            session_id: Session key to write.
            content: User message content.
            system_prompt: Optional seed prompt if the session is being created.
        """
        self.ensure_session(session_id, system_prompt)
        self._store[session_id].append(HumanMessage(content=content))

    def append_assistant(
        self, session_id: str, content: str, *, system_prompt: Optional[str] = None
    ) -> None:
        """Append an assistant turn (AIMessage), creating the session if needed.

        Args:
            session_id: Session key to write.
            content: Assistant message content.
            system_prompt: Optional seed prompt if the session is being created.
        """
        self.ensure_session(session_id, system_prompt)
        self._store[session_id].append(AIMessage(content=content))

    def append_turn(
        self,
        session_id: str,
        user_content: str,
        assistant_content: str,
        *,
        system_prompt: Optional[str] = None,
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
        self.ensure_session(session_id, system_prompt)
        self._store[session_id].extend(
            [HumanMessage(content=user_content), AIMessage(content=assistant_content)]
        )

    def clear(self, session_id: str) -> None:
        """Remove all messages for a session; no error if it does not exist.

        Args:
            session_id: Session key to delete.
        """
        self._store.pop(session_id, None)
