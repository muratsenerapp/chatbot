import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";
import InputBar from "./InputBar";
import type { ChatMessage } from "@/types/chat";
import { AlertTriangle, MessageCircle, RotateCw } from "lucide-react";
import { openSSE } from "@/lib/sse";

type Props = {
  /**
   * Optional custom handler; if provided, streaming here is bypassed.
   */
  onSend?: (
    input: string,
    messages: ChatMessage[],
  ) => Promise<ChatMessage | void> | ChatMessage | void;
};

// Match backend route exactly
const CHAT_STREAM_URL = "/api/chat/stream";

function newId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return String(Date.now()) + Math.random().toString(16).slice(2);
}

export default function Chat({ onSend }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [lastUserInput, setLastUserInput] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null); // optional

  const listRef = useRef<HTMLDivElement | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const esCloserRef = useRef<(() => void) | null>(null);
  const streamingAssistantId = useRef<string | null>(null);

  // Autoscroll when near the bottom
  useEffect(() => {
    const el = listRef.current;
    if (!el) return;
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 120;
    if (nearBottom) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  function pushUserMessage(text: string) {
    const userMsg: ChatMessage = { id: newId(), role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    return userMsg;
  }

  function createAssistantDraft() {
    const id = newId();
    streamingAssistantId.current = id;
    const draft: ChatMessage = { id, role: "assistant", content: "" };
    setMessages((prev) => [...prev, draft]);
    return draft;
  }

  function appendToAssistant(token: string) {
    const id = streamingAssistantId.current;
    if (!id || !token) return;
    setMessages((prev) =>
      prev.map((m) => (m.id === id ? { ...m, content: m.content + token } : m)),
    );
  }

  function markAssistantError(msg = "Sorry, something went wrong.") {
    const id = streamingAssistantId.current;
    if (!id) return;
    setMessages((prev) =>
      prev.map((m) => (m.id === id ? { ...m, content: msg, error: true } : m)),
    );
  }

  function clearStreamRefs() {
    setIsStreaming(false);
    esCloserRef.current = null;
    streamingAssistantId.current = null;
  }

  async function startStreaming(input: string) {
    setError(null);
    setIsStreaming(true);
    setLastUserInput(input);

    // 1) Push user message + create assistant draft
    const userMsg = pushUserMessage(input);
    createAssistantDraft();

    // 2) Open EventSource (GET /api/chat/stream?message=...&session_id=...)
    const closer = openSSE(CHAT_STREAM_URL, {
      params: {
        message: userMsg.content,
        session_id: sessionId || undefined,
      },
      onToken: (chunk) => {
        appendToAssistant(chunk);
      },
      onDone: (metrics) => {
        // Optionally store session_id if backend returns it
        if (metrics?.session_id && metrics.session_id !== sessionId) {
          setSessionId(metrics.session_id);
        }
        // Close handled by server (EOS) — we make sure to release refs
        clearStreamRefs();
      },
      onServerErrorEvent: (msg) => {
        // Server emitted `event: error`
        markAssistantError(msg || "Server error");
        setError(msg || "Request failed.");
        clearStreamRefs();
      },
      onNetworkError: () => {
        // Transport error (CORS, connection lost, etc.)
        markAssistantError("Network error.");
        setError("Network error. Please try again.");
        clearStreamRefs();
      },
      onClose: () => {
        // Called when we explicitly close (Stop)
        clearStreamRefs();
      },
    });

    esCloserRef.current = () => closer.close();
  }

  async function handleSubmit(text: string) {
    if (isStreaming) return;
    if (onSend) {
      // Non-stream fallback if a custom handler is wired
      setError(null);
      const userMsg = pushUserMessage(text);
      try {
        const maybe = await onSend(text, messages.concat(userMsg));
        if (maybe && typeof maybe === "object") {
          setMessages((prev) => [...prev, maybe]);
        }
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            id: newId(),
            role: "assistant",
            content: "Sorry, something went wrong.",
            error: true,
          },
        ]);
        setError("Failed to send. Please try again.");
      }
      return;
    }
    await startStreaming(text);
  }

  function handleAbort() {
    if (esCloserRef.current) {
      esCloserRef.current();
      esCloserRef.current = null;
    }
  }

  function handleRetry() {
    if (lastUserInput) {
      setError(null);
      startStreaming(lastUserInput);
    }
  }

  const isEmpty = messages.length === 0;

  return (
    <div className="flex h-[calc(100dvh-64px)] flex-col">
      {/* Messages */}
      <div
        ref={listRef}
        className="flex-1 space-y-4 overflow-y-auto py-6"
        aria-live="polite"
      >
        {isEmpty ? (
          <div className="grid h-full place-items-center">
            <div className="text-center text-slate-500">
              <div className="mb-2 inline-flex h-10 w-10 items-center justify-center rounded-full border dark:border-slate-700">
                <MessageCircle size={18} />
              </div>
              <p className="font-medium">No messages yet</p>
              <p className="text-sm">Start the conversation by sending one.</p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Error banner with retry */}
      {error && (
        <div className="mb-2 flex items-center justify-between gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
          <div className="flex items-center gap-2">
            <AlertTriangle size={16} aria-hidden />
            <span className="truncate">{error}</span>
          </div>
          <button
            onClick={handleRetry}
            className="inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs dark:border-red-800"
            aria-label="Retry last message"
          >
            <RotateCw size={14} />
            Retry
          </button>
        </div>
      )}

      {/* Input */}
      <div className="sticky bottom-0 bg-white pb-6 dark:bg-slate-950">
        <InputBar
          onSubmit={handleSubmit}
          isStreaming={isStreaming}
          onAbort={handleAbort}
        />
      </div>
    </div>
  );
}
