import { describe, it, vi, beforeAll, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import App from "@/App";

// jsdom ortamında window.matchMedia yok → ThemeToggle patlıyor.
// Burada basit bir mock ekliyoruz.
beforeAll(() => {
  if (!window.matchMedia) {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(), // deprecated
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
  }
});

describe("App", () => {
  it("renders the header, theme toggle, and chat input", () => {
    render(<App />);

    const title = screen.getByText("Chatbot");
    const themeSwitch = screen.getByRole("switch", {
      name: /toggle dark mode/i,
    });
    const input = screen.getByPlaceholderText("Type your message…");

    // Jest-DOM kullanmadan basit doğrulamalar
    expect(title).toBeDefined();
    expect(themeSwitch).toBeDefined();
    expect(input).toBeDefined();

    expect(title.textContent).toContain("Chatbot");
  });
});
