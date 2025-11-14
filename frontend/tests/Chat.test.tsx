import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import Chat from "@components/chat/Chat";

if (!(window.HTMLElement.prototype as any).scrollIntoView) {
  Object.defineProperty(window.HTMLElement.prototype, "scrollIntoView", {
    value: vi.fn(),
    writable: true,
    configurable: true,
  });
}

let lastSSEOptions: any;
let lastCloseFn: any;
let lastSSEUrl: string | undefined;

vi.mock("@/lib/sse", () => {
  return {
    openSSE: (url: string, opts: any) => {
      lastSSEUrl = url;
      lastSSEOptions = opts;

      const close = vi.fn((ev?: Event) => {
        if (opts && typeof opts.onClose === "function") {
          opts.onClose(ev);
        }
      });

      lastCloseFn = close;

      return {
        es: {} as EventSource,
        close,
      };
    },
  };
});

beforeEach(() => {
  lastSSEOptions = undefined;
  lastCloseFn = undefined;
  lastSSEUrl = undefined;
});

describe("Chat", () => {
  it("delegates sending to onSend when provided and appends assistant reply", async () => {
    const onSend = vi.fn().mockResolvedValue({
      id: "assistant-1",
      role: "assistant",
      content: "Mock reply",
    });

    render(<Chat onSend={onSend} />);

    const input = screen.getByPlaceholderText("Type your message…");

    fireEvent.change(input, { target: { value: "Hello" } });
    fireEvent.keyDown(input, {
      key: "Enter",
      code: "Enter",
      charCode: 13,
    });

    await screen.findByText("Hello");

    expect(onSend).toHaveBeenCalledTimes(1);
    expect(onSend.mock.calls[0][0]).toBe("Hello");

    await screen.findByText("Mock reply");
  });

  it("shows an error assistant message when onSend throws", async () => {
    const onSend = vi.fn().mockImplementation(() => {
      throw new Error("boom");
    });

    render(<Chat onSend={onSend} />);

    const input = screen.getByPlaceholderText("Type your message…");

    fireEvent.change(input, { target: { value: "Hi" } });
    fireEvent.keyDown(input, {
      key: "Enter",
      code: "Enter",
      charCode: 13,
    });

    await screen.findByText("Hi");
    await screen.findByText("Sorry, something went wrong.");
  });

  it("streams assistant reply via SSE and stops streaming on onDone", async () => {
    render(<Chat />);

    const input = screen.getByPlaceholderText("Type your message…");

    fireEvent.change(input, { target: { value: "stream this" } });
    fireEvent.keyDown(input, {
      key: "Enter",
      code: "Enter",
      charCode: 13,
    });

    await screen.findByText("stream this");

    const stopButton = await screen.findByRole("button", {
      name: /stop streaming/i,
    });
    expect(stopButton).toBeDefined();

    expect(lastSSEUrl).toBeDefined();
    expect(lastSSEOptions).toBeDefined();
    if (lastSSEOptions) {
      expect(lastSSEOptions.params.message).toBe("stream this");
    }

    act(() => {
      lastSSEOptions?.onToken?.("Hello ");
      lastSSEOptions?.onToken?.("world");
    });

    await screen.findByText("Hello world");

    act(() => {
      lastSSEOptions?.onDone?.({ session_id: "session-1" });
    });

    const stopAfter = screen.queryByRole("button", {
      name: /stop streaming/i,
    });
    expect(stopAfter).toBeNull();
  });

  it("aborts streaming and calls the SSE close function exactly once", async () => {
    render(<Chat />);

    const input = screen.getByPlaceholderText("Type your message…");

    fireEvent.change(input, { target: { value: "please abort" } });
    fireEvent.keyDown(input, {
      key: "Enter",
      code: "Enter",
      charCode: 13,
    });

    const stopButton = await screen.findByRole("button", {
      name: /stop streaming/i,
    });
    expect(stopButton).toBeDefined();
    expect(lastCloseFn).toBeDefined();

    fireEvent.click(stopButton);

    expect(lastCloseFn).toHaveBeenCalledTimes(1);

    const stopAfter = screen.queryByRole("button", {
      name: /stop streaming/i,
    });
    expect(stopAfter).toBeNull();
  });

  it("shows network error message when onNetworkError is triggered", async () => {
    render(<Chat />);

    const input = screen.getByPlaceholderText("Type your message…");

    fireEvent.change(input, { target: { value: "cause network error" } });
    fireEvent.keyDown(input, {
      key: "Enter",
      code: "Enter",
      charCode: 13,
    });

    await screen.findByText("cause network error");

    act(() => {
      lastSSEOptions?.onNetworkError?.(new Event("error"));
    });

    await screen.findByText("Network error. Please try again.");
    await screen.findByText("Network error.");

    const stopAfter = screen.queryByRole("button", {
      name: /stop streaming/i,
    });
    expect(stopAfter).toBeNull();
  });
});
