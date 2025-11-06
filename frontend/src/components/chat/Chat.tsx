import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";
import InputBar from "./InputBar";
import type { ChatMessage } from "@/types/chat";
import { AlertTriangle, MessageCircle } from "lucide-react";

type Props = {
  /** Optional send handler for backend integration */
  onSend?: (
    input: string,
    messages: ChatMessage[],
  ) => Promise<ChatMessage | void> | ChatMessage | void;
};

function newId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return String(Date.now()) + Math.random().toString(16).slice(2);
}

export default function Chat({ onSend }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  // Autoscroll when near the bottom
  useEffect(() => {
    const el = listRef.current;
    if (!el) return;
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 120;
    if (nearBottom) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  async function handleSubmit(text: string) {
    setError(null);
    const userMsg: ChatMessage = { id: newId(), role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);

    try {
      if (onSend) {
        const maybe = await onSend(text, messages.concat(userMsg));
        if (maybe && typeof maybe === "object") {
          setMessages((prev) => [...prev, maybe]);
        }
      } else {
        // Temporary mock reply until backend integration
        setTimeout(() => {
          setMessages((prev) => [
            ...prev,
            {
              id: newId(),
              role: "assistant",
              content:
                "This is a local mock reply. Replace with backend integration.",
            },
          ]);
        }, 150);
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
  }

  const isEmpty = messages.length === 0;

  return (
    <div className="flex h[calc(100dvh-64px)] flex-col">
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

      {/* Minimal error banner */}
      {error && (
        <div className="mb-2 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
          <AlertTriangle size={16} aria-hidden />
          <span className="truncate">{error}</span>
        </div>
      )}

      {/* Input */}
      <div className="sticky bottom-0 bg-white pb-6 dark:bg-slate-950">
        <InputBar onSubmit={handleSubmit} />
      </div>
    </div>
  );
}
