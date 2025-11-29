import { Bot, User } from "lucide-react";
import type { ChatMessage } from "@/types/chat";

/** Props for {@link MessageBubble}. */
type MessageBubbleProps = { message: ChatMessage };

/**
 * Chat message bubble with role-aware styling.
 *
 * @remarks Renders user vs assistant messages differently and supports an error state.
 * @public
 */
export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const baseStyles =
    "max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-2 text-sm shadow";
  const userStyles = "bg-blue-600 text-white dark:bg-blue-500";
  const assistantStyles =
    "bg-slate-100 text-slate-900 dark:bg-slate-900 dark:text-slate-100";
  const errorStyles =
    "border border-red-300 bg-red-50 text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200";

  return (
    <div
      className={`flex items-end gap-2 ${isUser ? "justify-end" : "justify-start"}`}
    >
      {!isUser && (
        <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-200">
          <Bot size={18} aria-hidden />
        </div>
      )}

      <div
        className={[
          baseStyles,
          isUser ? userStyles : assistantStyles,
          message.error ? errorStyles : "",
        ].join(" ")}
        role="group"
      >
        {message.content}
      </div>

      {isUser && (
        <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-blue-600 text-white dark:bg-blue-500">
          <User size={18} aria-hidden />
        </div>
      )}
    </div>
  );
}
