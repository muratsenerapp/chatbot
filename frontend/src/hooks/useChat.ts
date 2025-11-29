import { useCallback, useRef, useState } from "react";
import type { ChatMessage } from "@/types/chat";
import { openSSE } from "@lib/sseClient";
import { closeAndClear } from "@lib/streamUtils";
import { newId } from "@lib/idGenerator";

const CHAT_STREAM_URL = "/api/chat/stream";

/** Options for adding an assistant message. */
type AddAssistantMessageOptions = {
  /** If true, render with error styling. */
  error?: boolean;
};

/** Return type of {@link useChat}. */
export type UseChatReturn = {
  /** All chat messages. */
  messages: ChatMessage[];
  /** Current session ID from the backend. */
  sessionId: string | null;
  /** Whether a streaming request is in progress. */
  isStreaming: boolean;
  /** Current error message, if any. */
  error: string | null;
  /** Start streaming a message to the assistant. */
  startStreaming: (input: string) => void;
  /** Abort the current streaming request. */
  handleAbort: () => void;
  /** Retry the last user message. */
  handleRetry: () => void;
  /** Add a user message and return it. */
  pushUserMessage: (text: string) => ChatMessage;
  /** Add an assistant message. */
  addAssistantMessage: (
    content: string,
    options?: AddAssistantMessageOptions,
  ) => ChatMessage;
  /** Set the error message. */
  setError: (error: string | null) => void;
  /** Clear the error message. */
  clearError: () => void;
};

/**
 * Custom hook for managing chat state and SSE streaming.
 *
 * @remarks
 * Encapsulates all chat-related state including messages, session management,
 * streaming state, and error handling. Provides methods for starting/stopping
 * streams and managing messages.
 *
 * @returns Chat state and control methods.
 * @public
 */
export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [lastUserInput, setLastUserInput] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const esCloserRef = useRef<(() => void) | null>(null);
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

  const clearStreamRefs = useCallback((): void => {
    setIsStreaming(false);
    esCloserRef.current = null;
    streamingAssistantId.current = null;
  }, []);

  const startStreaming = useCallback(
    (input: string): void => {
      setError(null);
      setIsStreaming(true);
      setLastUserInput(input);

      const userMsg = pushUserMessage(input);
      createAssistantDraft();

      const closer = openSSE(CHAT_STREAM_URL, {
        params: {
          message: userMsg.content,
          session_id: sessionId || undefined,
        },
        onToken: (chunk) => {
          appendToAssistant(chunk);
        },
        onDone: (metrics) => {
          if (metrics?.session_id && metrics.session_id !== sessionId) {
            setSessionId(metrics.session_id);
          }
          clearStreamRefs();
        },
        onServerErrorEvent: (msg) => {
          markAssistantError(msg || "Server error");
          setError(msg || "Request failed.");
          clearStreamRefs();
        },
        onNetworkError: () => {
          markAssistantError("Network error.");
          setError("Network error. Please try again.");
          clearStreamRefs();
        },
        onClose: () => {
          clearStreamRefs();
        },
      });

      esCloserRef.current = () => closer.close();
    },
    [
      sessionId,
      pushUserMessage,
      createAssistantDraft,
      appendToAssistant,
      markAssistantError,
      clearStreamRefs,
    ],
  );

  const handleAbort = useCallback((): void => {
    closeAndClear(esCloserRef);
  }, []);

  const handleRetry = useCallback((): void => {
    if (lastUserInput) {
      setError(null);
      startStreaming(lastUserInput);
    }
  }, [lastUserInput, startStreaming]);

  const clearError = useCallback((): void => {
    setError(null);
  }, []);

  return {
    messages,
    sessionId,
    isStreaming,
    error,
    startStreaming,
    handleAbort,
    handleRetry,
    pushUserMessage,
    addAssistantMessage,
    setError,
    clearError,
  };
}
