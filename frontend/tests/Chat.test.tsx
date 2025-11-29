import Chat from "@components/chat/Chat";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach,describe, expect, it, vi } from "vitest";

if (!(window.HTMLElement.prototype as any).scrollIntoView) {
  Object.defineProperty(window.HTMLElement.prototype, "scrollIntoView", {
    value: vi.fn(),
    writable: true,
    configurable: true,
  });
}

const mockUseChat = {
  messages: [] as any[],
  sessionId: null as string | null,
  isStreaming: false,
  error: null as string | null,
  startStreaming: vi.fn(),
  handleAbort: vi.fn(),
  handleRetry: vi.fn(),
  pushUserMessage: vi.fn((text: string) => ({
    id: "user-msg-id",
    role: "user",
    content: text,
  })),
  addAssistantMessage: vi.fn((content: string, options?: any) => ({
    id: "assistant-msg-id",
    role: "assistant",
    content,
    error: options?.error,
  })),
  setError: vi.fn(),
  clearError: vi.fn(),
};

vi.mock("@/hooks/useChat", () => ({
  useChat: () => mockUseChat,
}));

beforeEach(() => {
  mockUseChat.messages = [];
  mockUseChat.sessionId = null;
  mockUseChat.isStreaming = false;
  mockUseChat.error = null;
  mockUseChat.startStreaming.mockClear();
  mockUseChat.handleAbort.mockClear();
  mockUseChat.handleRetry.mockClear();
  mockUseChat.pushUserMessage.mockClear();
  mockUseChat.addAssistantMessage.mockClear();
  mockUseChat.setError.mockClear();
  mockUseChat.clearError.mockClear();

  mockUseChat.pushUserMessage.mockImplementation((text: string) => ({
    id: "user-msg-id",
    role: "user",
    content: text,
  }));
});

describe("Chat", () => {
  describe("empty state", () => {
    it("shows empty state message when no messages", () => {
      render(<Chat />);

      expect(screen.getByText("No messages yet")).toBeInTheDocument();
      expect(
        screen.getByText("Start the conversation by sending one."),
      ).toBeInTheDocument();
    });
  });

  describe("message rendering", () => {
    it("renders messages when present", () => {
      mockUseChat.messages = [
        { id: "1", role: "user", content: "Hello" },
        { id: "2", role: "assistant", content: "Hi there!" },
      ];

      render(<Chat />);

      expect(screen.getByText("Hello")).toBeInTheDocument();
      expect(screen.getByText("Hi there!")).toBeInTheDocument();
    });
  });

  describe("error banner", () => {
    it("shows error banner when error exists", () => {
      mockUseChat.error = "Something went wrong";

      render(<Chat />);

      expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    });

    it("calls handleRetry when retry button is clicked", () => {
      mockUseChat.error = "Network error";

      render(<Chat />);

      const retryButton = screen.getByRole("button", {
        name: /retry last message/i,
      });
      fireEvent.click(retryButton);

      expect(mockUseChat.handleRetry).toHaveBeenCalledTimes(1);
    });

    it("does not show error banner when no error", () => {
      render(<Chat />);

      expect(screen.queryByRole("button", { name: /retry/i })).toBeNull();
    });
  });

  describe("streaming state", () => {
    it("shows stop button when streaming", () => {
      mockUseChat.isStreaming = true;

      render(<Chat />);

      expect(
        screen.getByRole("button", { name: /stop streaming/i }),
      ).toBeInTheDocument();
    });

    it("calls handleAbort when stop button is clicked", () => {
      mockUseChat.isStreaming = true;

      render(<Chat />);

      const stopButton = screen.getByRole("button", {
        name: /stop streaming/i,
      });
      fireEvent.click(stopButton);

      expect(mockUseChat.handleAbort).toHaveBeenCalledTimes(1);
    });
  });

  describe("onSend callback", () => {
    it("delegates sending to onSend when provided", async () => {
      const onSend = vi.fn().mockResolvedValue({
        id: "assistant-1",
        role: "assistant",
        content: "Mock reply",
      });

      render(<Chat onSend={onSend} />);

      const input = screen.getByPlaceholderText("Type your message…");
      fireEvent.change(input, { target: { value: "Hello" } });
      fireEvent.keyDown(input, { key: "Enter", code: "Enter", charCode: 13 });

      await waitFor(() => {
        expect(mockUseChat.clearError).toHaveBeenCalled();
        expect(mockUseChat.pushUserMessage).toHaveBeenCalledWith("Hello");
        expect(onSend).toHaveBeenCalledTimes(1);
        expect(onSend.mock.calls[0][0]).toBe("Hello");
      });
    });

    it("adds assistant message when onSend returns a message", async () => {
      const onSend = vi.fn().mockResolvedValue({
        id: "assistant-1",
        role: "assistant",
        content: "Mock reply",
      });

      render(<Chat onSend={onSend} />);

      const input = screen.getByPlaceholderText("Type your message…");
      fireEvent.change(input, { target: { value: "Hello" } });
      fireEvent.keyDown(input, { key: "Enter", code: "Enter", charCode: 13 });

      await waitFor(() => {
        expect(mockUseChat.addAssistantMessage).toHaveBeenCalledWith(
          "Mock reply",
          { error: undefined },
        );
      });
    });

    it("shows error message when onSend throws", async () => {
      const onSend = vi.fn().mockRejectedValue(new Error("boom"));

      render(<Chat onSend={onSend} />);

      const input = screen.getByPlaceholderText("Type your message…");
      fireEvent.change(input, { target: { value: "Hello" } });
      fireEvent.keyDown(input, { key: "Enter", code: "Enter", charCode: 13 });

      await waitFor(() => {
        expect(mockUseChat.addAssistantMessage).toHaveBeenCalledWith(
          "Sorry, something went wrong.",
          { error: true },
        );
        expect(mockUseChat.setError).toHaveBeenCalledWith(
          "Failed to send. Please try again.",
        );
      });
    });

    it("does not call onSend when onSend is not provided", async () => {
      render(<Chat />);

      const input = screen.getByPlaceholderText("Type your message…");
      fireEvent.change(input, { target: { value: "Hello" } });
      fireEvent.keyDown(input, { key: "Enter", code: "Enter", charCode: 13 });

      await waitFor(() => {
        expect(mockUseChat.startStreaming).toHaveBeenCalledWith("Hello");
      });
    });
  });

  describe("submit behavior", () => {
    it("does not submit when streaming is in progress", async () => {
      mockUseChat.isStreaming = true;

      render(<Chat />);

      const input = screen.getByPlaceholderText("Type your message…");
      fireEvent.change(input, { target: { value: "Hello" } });
      fireEvent.keyDown(input, { key: "Enter", code: "Enter", charCode: 13 });

      expect(mockUseChat.startStreaming).not.toHaveBeenCalled();
    });
  });
});
