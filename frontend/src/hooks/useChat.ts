import { useCallback, useState } from "react";

import type { ChatMessage } from "@/types/chat";

import { type AddAssistantMessageOptions, useMessages } from "./useMessages";
import { useSSEStream } from "./useSSEStream";

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
 * Composes {@link useMessages} and {@link useSSEStream} to provide
 * complete chat functionality including messages, session management,
 * streaming state, and error handling.
 *
 * @returns Chat state and control methods.
 * @public
 */
export function useChat(): UseChatReturn {
  const {
    messages,
    pushUserMessage,
    addAssistantMessage,
    createAssistantDraft,
    appendToAssistant,
    markAssistantError,
    streamingAssistantId,
  } = useMessages();

  const { isStreaming, startStream, abortStream } = useSSEStream();

  const [error, setError] = useState<string | null>(null);
  const [lastUserInput, setLastUserInput] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const startStreaming = useCallback(
    (input: string): void => {
      setError(null);
      setLastUserInput(input);

      const userMsg = pushUserMessage(input);
      createAssistantDraft();

      startStream(
        {
          message: userMsg.content,
          sessionId,
        },
        {
          onToken: (chunk) => {
            appendToAssistant(chunk);
          },
          onDone: (metrics) => {
            if (metrics?.session_id && metrics.session_id !== sessionId) {
              setSessionId(metrics.session_id);
            }
            streamingAssistantId.current = null;
          },
          onServerError: (msg) => {
            markAssistantError(msg || "Server error");
            setError(msg || "Request failed.");
            streamingAssistantId.current = null;
          },
          onNetworkError: () => {
            markAssistantError("Network error.");
            setError("Network error. Please try again.");
            streamingAssistantId.current = null;
          },
          onClose: () => {
            streamingAssistantId.current = null;
          },
        },
      );
    },
    [
      sessionId,
      pushUserMessage,
      createAssistantDraft,
      startStream,
      appendToAssistant,
      markAssistantError,
      streamingAssistantId,
    ],
  );

  const handleAbort = useCallback((): void => {
    abortStream();
  }, [abortStream]);

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
