import { useEffect, useRef, useState } from "react";
import { SendHorizontal, Square } from "lucide-react";

type Props = {
  onSubmit: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
  isStreaming?: boolean;
  onAbort?: () => void;
};

export default function InputBar({
  onSubmit,
  disabled = false,
  placeholder = "Type your message…",
  isStreaming = false,
  onAbort,
}: Props) {
  const [value, setValue] = useState("");
  const taRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    const el = taRef.current;
    if (!el) return;
    el.style.height = "0px";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, [value]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey && !isStreaming) {
      e.preventDefault();
      trySubmit();
    }
  }

  function trySubmit() {
    const text = value.trim();
    if (!text || isStreaming) return;
    onSubmit(text);
    setValue("");
  }

  const canSend = value.trim().length > 0 && !disabled && !isStreaming;

  return (
    <div className="rounded-xl border bg-white p-2 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <label htmlFor="chat-input" className="sr-only">
        Message
      </label>
      <div className="flex items-end gap-2">
        <textarea
          id="chat-input"
          ref={taRef}
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
      <div className="mt-1 pl-2 text-[11px] text-slate-500">
        Enter: send • Shift+Enter: new line
      </div>
    </div>
  );
}
