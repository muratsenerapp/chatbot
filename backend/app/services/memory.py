from __future__ import annotations

from typing import Dict, List, Optional

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage


class SessionMemory:
    """In-memory session-scoped chat history.

    Simple process-local store: NOT persisted, NOT multi-process safe.
    """

    def __init__(self, default_system_prompt: Optional[str] = None) -> None:
        self._default_system_prompt = default_system_prompt
        self._store: Dict[str, List[BaseMessage]] = {}

    def ensure_session(
        self, session_id: str, system_prompt: Optional[str] = None
    ) -> None:
        """Create the session buffer with an optional SystemMessage when missing."""
        if session_id not in self._store:
            sp = system_prompt or self._default_system_prompt
            self._store[session_id] = [SystemMessage(content=sp)] if sp else []

    def get_messages(self, session_id: str) -> List[BaseMessage]:
        """Return a shallow copy to avoid external mutation."""
        return list(self._store.get(session_id, []))

    def append_user(
        self, session_id: str, content: str, *, system_prompt: Optional[str] = None
    ) -> None:
        self.ensure_session(session_id, system_prompt)
        self._store[session_id].append(HumanMessage(content=content))

    def append_assistant(
        self, session_id: str, content: str, *, system_prompt: Optional[str] = None
    ) -> None:
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
        self.ensure_session(session_id, system_prompt)
        self._store[session_id].extend(
            [HumanMessage(content=user_content), AIMessage(content=assistant_content)]
        )

    def clear(self, session_id: str) -> None:
        self._store.pop(session_id, None)
