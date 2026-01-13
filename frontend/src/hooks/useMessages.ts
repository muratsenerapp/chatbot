import { useCallback, useRef, useState } from "react";

import { newId } from "@/lib/idGenerator";
import type { ChatMessage } from "@/types/chat";

/** Options for adding an assistant message. */
export type AddAssistantMessageOptions = {
  /** If true, render with error styling. */
  error?: boolean;
};

/** Return type of {@link useMessages}. */
export type UseMessagesReturn = {
  /** All chat messages. */
  messages: ChatMessage[];
  /** Add a user message and return it. */
  pushUserMessage: (text: string) => ChatMessage;
  /** Add an assistant message. */
  addAssistantMessage: (
    content: string,
    options?: AddAssistantMessageOptions,
  ) => ChatMessage;
  /** Create an empty assistant message draft for streaming. */
  createAssistantDraft: () => ChatMessage;
  /** Append a token to the current streaming assistant message. */
  appendToAssistant: (token: string) => void;
  /** Mark the current streaming assistant message as an error. */
  markAssistantError: (message?: string) => void;
  /** ID of the current streaming assistant message. */
  streamingAssistantId: React.MutableRefObject<string | null>;
};

/**
 * Hook for managing chat messages state.
 *
 * @remarks
 * Encapsulates message state including adding user/assistant messages,
 * creating streaming drafts, and updating streaming content.
 *
 * @returns Message state and control methods.
 * @public
 */
export function useMessages(): UseMessagesReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const streamingAssistantId = useRef<string | null>(null);

  const pushUserMessage = useCallback((text: string): ChatMessage => {
    const userMsg: ChatMessage = { id: newId(), role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    return userMsg;
  }, []);

  const addAssistantMessage = useCallback(
    (content: string, options?: AddAssistantMessageOptions): ChatMessage => {
      const msg: ChatMessage = {
        id: newId(),
        role: "assistant",
        content,
        error: options?.error,
      };
      setMessages((prev) => [...prev, msg]);
      return msg;
    },
    [],
  );

  const createAssistantDraft = useCallback((): ChatMessage => {
    const id = newId();
    streamingAssistantId.current = id;
    const draft: ChatMessage = { id, role: "assistant", content: "" };
    setMessages((prev) => [...prev, draft]);
    return draft;
  }, []);

  const appendToAssistant = useCallback((token: string): void => {
    const id = streamingAssistantId.current;
    if (!id || !token) return;
    setMessages((prev) =>
      prev.map((m) => (m.id === id ? { ...m, content: m.content + token } : m)),
    );
  }, []);

  const markAssistantError = useCallback(
    (msg = "Sorry, something went wrong."): void => {
      const id = streamingAssistantId.current;
      if (!id) return;
      setMessages((prev) =>
        prev.map((m) =>
          m.id === id ? { ...m, content: msg, error: true } : m,
        ),
      );
    },
    [],
  );

  return {
    messages,
    pushUserMessage,
    addAssistantMessage,
    createAssistantDraft,
    appendToAssistant,
    markAssistantError,
    streamingAssistantId,
  };
}
