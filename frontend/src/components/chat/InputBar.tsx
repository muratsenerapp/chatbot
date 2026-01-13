import { useEffect, useRef, useState } from "react";

import { SendHorizontal, Square } from "lucide-react";

/** Default maximum character length for messages. */
const DEFAULT_MAX_LENGTH = 4000;

/** Props for {@link InputBar}. */
type InputBarProps = {
  /** Send callback invoked on submit. */
  onSubmit: (text: string) => void;
  /** Disables the input and buttons. */
  disabled?: boolean;
  /** Placeholder text for the input. */
  placeholder?: string;
  /** When true, shows an abort button and prevents new submits. */
  isStreaming?: boolean;
  /** Abort handler for an in-flight request. */
  onAbort?: () => void;
  /** Maximum character length for messages. Defaults to 4000. */
  maxLength?: number;
};

/**
 * Compact message composer with keyboard submit and abort affordance.
 *
 * @remarks Blocks additional submissions while `isStreaming` is true.
 * @public
 */
export default function InputBar({
  onSubmit,
  disabled = false,
  placeholder = "Type your message…",
  isStreaming = false,
  onAbort,
  maxLength = DEFAULT_MAX_LENGTH,
}: InputBarProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const charCount = value.length;
  const isOverLimit = charCount > maxLength;
  const isNearLimit = charCount >= maxLength * 0.9;

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "0px";
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + "px";
  }, [value]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey && !isStreaming) {
      e.preventDefault();
      trySubmit();
    }
  }

  function trySubmit() {
    const text = value.trim();
    if (!text || isStreaming || isOverLimit) return;
    onSubmit(text);
    setValue("");
  }

  const canSend =
    value.trim().length > 0 && !disabled && !isStreaming && !isOverLimit;

  return (
    <div
      className={`rounded-xl border bg-white p-2 shadow-sm dark:bg-slate-900 ${
        isOverLimit
          ? "border-red-400 dark:border-red-500"
          : "dark:border-slate-700"
      }`}
    >
      <label htmlFor="chat-input" className="sr-only">
        Message
      </label>
      <div className="flex items-end gap-2">
        <textarea
          id="chat-input"
          ref={textareaRef}
          className="max-h-[200px] w-full resize-none bg-transparent p-2 outline-none placeholder:text-slate-400 dark:placeholder:text-slate-500"
          rows={1}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || isStreaming}
          aria-disabled={disabled || isStreaming}
        />

        {isStreaming ? (
          <button
            type="button"
            onClick={onAbort}
            className="grid h-9 w-9 place-items-center rounded-lg border text-slate-600 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
            aria-label="Stop streaming"
          >
            <Square size={18} />
          </button>
        ) : (
          <button
            type="button"
            onClick={trySubmit}
            className={`grid h-9 w-9 place-items-center rounded-lg border text-slate-600 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 ${!canSend ? "pointer-events-none opacity-50" : ""}`}
            aria-label="Send"
          >
            <SendHorizontal size={18} />
          </button>
        )}
      </div>
      <div className="mt-1 flex items-center justify-between px-2 text-[11px] text-slate-500">
        <span>Enter: send • Shift+Enter: new line</span>
        <span
          className={
            isOverLimit
              ? "font-medium text-red-500"
              : isNearLimit
                ? "text-amber-500 dark:text-amber-400"
                : ""
          }
          aria-live="polite"
        >
          {charCount.toLocaleString()}/{maxLength.toLocaleString()}
        </span>
      </div>
    </div>
  );
}
