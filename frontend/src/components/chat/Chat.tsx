import { useEffect, useRef } from "react";

import { AlertTriangle, MessageCircle, RotateCw } from "lucide-react";

import { useChat } from "@/hooks";
import type { ChatMessage } from "@/types";

import InputBar from "./InputBar";
import MessageBubble from "./MessageBubble";

/** Props for {@link Chat}. */
type ChatProps = {
  /** Optional custom send handler; bypasses built-in SSE. */
  onSend?: (
    input: string,
    messages: ChatMessage[],
  ) => Promise<ChatMessage | void> | ChatMessage | void;
};

/**
 * Stateful chat container that streams tokens from the backend by default.
 *
 * @remarks If `onSend` is provided, the component delegates sending to it and skips SSE.
 * Cleans up any open streams on unmount.
 * @public
 */
export default function Chat({ onSend }: ChatProps) {
  const {
    messages,
    isStreaming,
    error,
    startStreaming,
    handleAbort,
    handleRetry,
    pushUserMessage,
    addAssistantMessage,
    setError,
    clearError,
  } = useChat();

  const listRef = useRef<HTMLDivElement | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const el = listRef.current;
    if (!el) return;
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 120;
    if (nearBottom) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  async function handleSubmit(text: string) {
    if (isStreaming) return;

    if (onSend) {
      clearError();
      const userMsg = pushUserMessage(text);
      try {
        const maybe = await onSend(text, messages.concat(userMsg));
        if (maybe && typeof maybe === "object") {
          addAssistantMessage(maybe.content, { error: maybe.error });
        }
      } catch {
        addAssistantMessage("Sorry, something went wrong.", { error: true });
        setError("Failed to send. Please try again.");
      }
      return;
    }

    startStreaming(text);
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
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
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
