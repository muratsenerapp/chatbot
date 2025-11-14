import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import MessageBubble from "@components/chat/MessageBubble";
import type { ChatMessage } from "@/types/chat";

describe("MessageBubble", () => {
  it("renders a user message aligned to the end with user styling", () => {
    const msg: ChatMessage = {
      id: "1",
      role: "user",
      content: "Hello from user",
    };

    const { container } = render(<MessageBubble message={msg} />);

    // Outer wrapper should align to end for user
    const wrapper = container.firstElementChild as HTMLElement;
    expect(wrapper.className).toContain("justify-end");

    // Bubble content should be rendered with user styling
    const bubble = screen.getByText("Hello from user");

    // Jest-dom kullanmadan varlığını ve içeriğini kontrol ediyoruz
    expect(bubble).toBeDefined();
    expect(bubble.textContent).toBe("Hello from user");

    // User bubble should have blue background
    expect(bubble.className).toContain("bg-blue-600");
  });

  it("renders an assistant error message with error styling", () => {
    const msg: ChatMessage = {
      id: "2",
      role: "assistant",
      content: "Something went wrong",
      error: true,
    };

    const { container } = render(<MessageBubble message={msg} />);

    const wrapper = container.firstElementChild as HTMLElement;
    expect(wrapper.className).toContain("justify-start");

    const bubble = screen.getByText("Something went wrong");

    // Varlık ve içerik kontrolü (jest-dom yok)
    expect(bubble).toBeDefined();
    expect(bubble.textContent).toBe("Something went wrong");

    // Error stilinin bazı sınıflarını kontrol edelim
    expect(bubble.className).toMatch(/bg-red-50/);
    expect(bubble.className).toMatch(/border-red-300/);
  });
});
