import { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";

type Theme = "light" | "dark";

function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "light";
  const stored = localStorage.getItem("theme");
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

/**
 * Theme switch for toggling light/dark mode.
 *
 * @remarks Persists preference in `localStorage` and syncs with system color scheme.
 * @public
 */
export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle("dark", theme === "dark");
    localStorage.setItem("theme", theme);
  }, [theme]);

  const isDark = theme === "dark";

  return (
    <div className="flex items-center gap-2">
      {isDark ? (
        <Moon className="h-4 w-4" aria-hidden />
      ) : (
        <Sun className="h-4 w-4" aria-hidden />
      )}

      <button
        type="button"
        role="switch"
        aria-checked={isDark}
        aria-label="Toggle dark mode"
        onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
        className="relative inline-flex h-7 w-12 items-center rounded-full border border-slate-300 bg-slate-200 transition dark:border-slate-700 dark:bg-slate-800"
      >
        <span
          className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow transition ${
            isDark ? "translate-x-6" : "translate-x-1"
          }`}
        />
        <span className="sr-only">
          {isDark ? "Switch to light" : "Switch to dark"}
        </span>
      </button>
    </div>
  );
}
