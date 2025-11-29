import MessageBubble from "@components/chat/MessageBubble";
import { render, screen } from "@testing-library/react";
import { describe, expect,it } from "vitest";

import type { ChatMessage } from "@/types/chat";

describe("MessageBubble", () => {
  it("renders a user message aligned to the end with user styling", () => {
    const msg: ChatMessage = {
      id: "1",
      role: "user",
      content: "Hello from user",
    };

    const { container } = render(<MessageBubble message={msg} />);

    const wrapper = container.firstElementChild as HTMLElement;
    expect(wrapper.className).toContain("justify-end");

    const bubble = screen.getByText("Hello from user");

    expect(bubble).toBeDefined();
    expect(bubble.textContent).toBe("Hello from user");

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

    expect(bubble).toBeDefined();
    expect(bubble.textContent).toBe("Something went wrong");

    expect(bubble.className).toMatch(/bg-red-50/);
    expect(bubble.className).toMatch(/border-red-300/);
  });
});
