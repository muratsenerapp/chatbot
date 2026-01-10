import { useCallback, useEffect, useRef, useState } from "react";

import { openSSE, type OpenSSEOptions } from "@/lib/sseClient";
import { closeAndClear } from "@/lib/streamUtils";

const CHAT_STREAM_URL = "/api/chat/stream";

/** Parameters for starting an SSE stream. */
export type StartStreamParams = {
  /** The message to send. */
  message: string;
  /** Optional session ID. */
  sessionId?: string | null;
};

/** Callbacks for SSE stream events. */
export type StreamCallbacks = {
  /** Called when a token chunk is received. */
  onToken?: (chunk: string) => void;
  /** Called when streaming completes successfully. */
  onDone?: (
    metrics: {
      session_id?: string | null;
      chars: number;
      elapsed_ms: number;
    } | null,
  ) => void;
  /** Called when a server error event is received. */
  onServerError?: (message: string) => void;
  /** Called when a network error occurs. */
  onNetworkError?: () => void;
  /** Called when the stream closes (always). */
  onClose?: () => void;
};

/** Return type of {@link useSSEStream}. */
export type UseSSEStreamReturn = {
  /** Whether a streaming request is in progress. */
  isStreaming: boolean;
  /** Start a new SSE stream with the given params and callbacks. */
  startStream: (params: StartStreamParams, callbacks: StreamCallbacks) => void;
  /** Abort the current streaming request. */
  abortStream: () => void;
};

/**
 * Hook for managing SSE streaming connections.
 *
 * @remarks
 * Encapsulates SSE connection state including opening/closing streams
 * and handling stream lifecycle events.
 *
 * @returns Streaming state and control methods.
 * @public
 */
export function useSSEStream(): UseSSEStreamReturn {
  const [isStreaming, setIsStreaming] = useState(false);
  const esCloserRef = useRef<(() => void) | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      closeAndClear(esCloserRef);
    };
  }, []);

  const clearStreamState = useCallback((): void => {
    setIsStreaming(false);
    esCloserRef.current = null;
  }, []);

  const startStream = useCallback(
    (params: StartStreamParams, callbacks: StreamCallbacks): void => {
      setIsStreaming(true);

      const sseOptions: OpenSSEOptions = {
        params: {
          message: params.message,
          session_id: params.sessionId || undefined,
        },
        onToken: (chunk) => {
          callbacks.onToken?.(chunk);
        },
        onDone: (metrics) => {
          callbacks.onDone?.(metrics);
          clearStreamState();
        },
        onServerErrorEvent: (msg) => {
          callbacks.onServerError?.(msg);
          clearStreamState();
        },
        onNetworkError: () => {
          callbacks.onNetworkError?.();
          clearStreamState();
        },
        onClose: () => {
          callbacks.onClose?.();
          clearStreamState();
        },
      };

      const closer = openSSE(CHAT_STREAM_URL, sseOptions);
      esCloserRef.current = () => closer.close();
    },
    [clearStreamState],
  );

  const abortStream = useCallback((): void => {
    closeAndClear(esCloserRef);
  }, []);

  return {
    isStreaming,
    startStream,
    abortStream,
  };
}
