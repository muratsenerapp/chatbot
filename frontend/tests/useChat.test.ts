import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useChat } from "@/hooks/useChat";

let lastSSEOptions: any;
let lastCloseFn: any;
let lastSSEUrl: string | undefined;

vi.mock("@/lib/sseClient", () => {
  return {
    openSSE: (url: string, opts: any) => {
      lastSSEUrl = url;
      lastSSEOptions = opts;

      const close = vi.fn((ev?: Event) => {
        if (opts && typeof opts.onClose === "function") {
          opts.onClose(ev);
        }
      });

      lastCloseFn = close;

      return {
        es: {} as EventSource,
        close,
      };
    },
  };
});

beforeEach(() => {
  lastSSEOptions = undefined;
  lastCloseFn = undefined;
  lastSSEUrl = undefined;
});

describe("useChat", () => {
  describe("initial state", () => {
    it("returns empty messages array initially", () => {
      const { result } = renderHook(() => useChat());

      expect(result.current.messages).toEqual([]);
    });

    it("returns null sessionId initially", () => {
      const { result } = renderHook(() => useChat());

      expect(result.current.sessionId).toBeNull();
    });

    it("returns isStreaming false initially", () => {
      const { result } = renderHook(() => useChat());

      expect(result.current.isStreaming).toBe(false);
    });

    it("returns null error initially", () => {
      const { result } = renderHook(() => useChat());

      expect(result.current.error).toBeNull();
    });
  });

  describe("pushUserMessage", () => {
    it("adds a user message to messages array", () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.pushUserMessage("Hello");
      });

      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0].role).toBe("user");
      expect(result.current.messages[0].content).toBe("Hello");
    });

    it("returns the created message", () => {
      const { result } = renderHook(() => useChat());

      let returnedMessage: any;
      act(() => {
        returnedMessage = result.current.pushUserMessage("Test message");
      });

      expect(returnedMessage).toBeDefined();
      expect(returnedMessage.id).toBeDefined();
      expect(returnedMessage.role).toBe("user");
      expect(returnedMessage.content).toBe("Test message");
    });
  });

  describe("addAssistantMessage", () => {
    it("adds an assistant message to messages array", () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.addAssistantMessage("Hello from assistant");
      });

      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0].role).toBe("assistant");
      expect(result.current.messages[0].content).toBe("Hello from assistant");
    });

    it("adds an error assistant message when error option is true", () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.addAssistantMessage("Something went wrong", {
          error: true,
        });
      });

      expect(result.current.messages[0].error).toBe(true);
    });
  });

  describe("error management", () => {
    it("sets error via setError", () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.setError("Test error");
      });

      expect(result.current.error).toBe("Test error");
    });

    it("clears error via clearError", () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.setError("Test error");
      });

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe("startStreaming", () => {
    it("sets isStreaming to true", () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.startStreaming("Hello");
      });

      expect(result.current.isStreaming).toBe(true);
    });

    it("adds user message and empty assistant draft", () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.startStreaming("Hello");
      });

      expect(result.current.messages).toHaveLength(2);
      expect(result.current.messages[0].role).toBe("user");
      expect(result.current.messages[0].content).toBe("Hello");
      expect(result.current.messages[1].role).toBe("assistant");
      expect(result.current.messages[1].content).toBe("");
    });

    it("opens SSE connection with correct URL", () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.startStreaming("Test message");
      });

      expect(lastSSEUrl).toBe("/api/chat/stream");
      expect(lastSSEOptions.params.message).toBe("Test message");
    });

    it("clears existing error when starting stream", () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.setError("Previous error");
      });

      act(() => {
        result.current.startStreaming("Hello");
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe("streaming tokens", () => {
    it("appends tokens to assistant message", () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.startStreaming("Hello");
      });

      act(() => {
        lastSSEOptions?.onToken?.("World ");
        lastSSEOptions?.onToken?.("!");
      });

      expect(result.current.messages[1].content).toBe("World !");
    });

    it("updates sessionId on done event", () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.startStreaming("Hello");
      });

      act(() => {
        lastSSEOptions?.onDone?.({ session_id: "new-session-123" });
      });

      expect(result.current.sessionId).toBe("new-session-123");
    });

    it("sets isStreaming to false on done", () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.startStreaming("Hello");
      });

      act(() => {
        lastSSEOptions?.onDone?.({ session_id: "session-1" });
      });

      expect(result.current.isStreaming).toBe(false);
    });
  });

  describe("handleAbort", () => {
    it("calls SSE close function", () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.startStreaming("Hello");
      });

      act(() => {
        result.current.handleAbort();
      });

      expect(lastCloseFn).toHaveBeenCalledTimes(1);
    });

    it("sets isStreaming to false after abort", () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.startStreaming("Hello");
      });

      act(() => {
        result.current.handleAbort();
      });

      expect(result.current.isStreaming).toBe(false);
    });
  });

  describe("error handling", () => {
    it("handles network error", () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.startStreaming("Hello");
      });

      act(() => {
        lastSSEOptions?.onNetworkError?.(new Event("error"));
      });

      expect(result.current.error).toBe("Network error. Please try again.");
      expect(result.current.messages[1].error).toBe(true);
      expect(result.current.messages[1].content).toBe("Network error.");
      expect(result.current.isStreaming).toBe(false);
    });

    it("handles server error", () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.startStreaming("Hello");
      });

      act(() => {
        lastSSEOptions?.onServerErrorEvent?.("Internal server error");
      });

      expect(result.current.error).toBe("Internal server error");
      expect(result.current.messages[1].error).toBe(true);
      expect(result.current.isStreaming).toBe(false);
    });
  });

  describe("handleRetry", () => {
    it("retries with the last user input", () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.startStreaming("First message");
      });

      act(() => {
        lastSSEOptions?.onNetworkError?.(new Event("error"));
      });

      act(() => {
        result.current.handleRetry();
      });

      expect(result.current.messages).toHaveLength(4);
      expect(result.current.messages[2].content).toBe("First message");
      expect(result.current.isStreaming).toBe(true);
    });

    it("clears error when retrying", () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.startStreaming("Test");
      });

      act(() => {
        lastSSEOptions?.onNetworkError?.(new Event("error"));
      });

      expect(result.current.error).not.toBeNull();

      act(() => {
        result.current.handleRetry();
      });

      expect(result.current.error).toBeNull();
    });

    it("does nothing if no previous message exists", () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.handleRetry();
      });

      expect(result.current.messages).toHaveLength(0);
      expect(result.current.isStreaming).toBe(false);
    });
  });

  describe("session management", () => {
    it("sends session_id in subsequent requests", () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.startStreaming("First message");
      });

      act(() => {
        lastSSEOptions?.onDone?.({ session_id: "session-abc" });
      });

      act(() => {
        result.current.startStreaming("Second message");
      });

      expect(lastSSEOptions.params.session_id).toBe("session-abc");
    });
  });
});
