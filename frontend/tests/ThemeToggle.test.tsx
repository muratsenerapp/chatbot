import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ThemeToggle from "@/components/theme-toggle";

function mockMatchMedia(matches: boolean) {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
}

function getSwitch(): HTMLButtonElement {
  return screen.getByRole("switch", {
    name: /toggle dark mode/i,
  }) as HTMLButtonElement;
}

function expectTheme(isDark: boolean) {
  const btn = getSwitch();

  const ariaChecked = btn.getAttribute("aria-checked");
  expect(ariaChecked).toBe(isDark ? "true" : "false");

  const hasDarkClass = document.documentElement.classList.contains("dark");
  expect(hasDarkClass).toBe(isDark);

  const stored = localStorage.getItem("theme");
  expect(stored).toBe(isDark ? "dark" : "light");
}

beforeEach(() => {
  document.documentElement.className = "";
  localStorage.clear();
  vi.resetAllMocks();
});

describe("ThemeToggle", () => {
  it("uses system dark preference when no stored theme exists", () => {
    mockMatchMedia(true);

    render(<ThemeToggle />);

    expectTheme(true);
  });

  it("prefers stored theme over system preference", () => {
    localStorage.setItem("theme", "light");
    mockMatchMedia(true);

    render(<ThemeToggle />);

    expectTheme(false);
  });

  it("toggles between light and dark and persists to localStorage", () => {
    localStorage.setItem("theme", "light");
    mockMatchMedia(false);

    render(<ThemeToggle />);

    expectTheme(false);

    const btn = getSwitch();
    fireEvent.click(btn);

    expectTheme(true);

    fireEvent.click(btn);

    expectTheme(false);
  });
});
