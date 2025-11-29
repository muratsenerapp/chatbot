import InputBar from "@components/chat/InputBar";
import { fireEvent,render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

describe("InputBar", () => {
  it("submits trimmed text on Enter and clears the textarea", () => {
    const handleSubmit = vi.fn();

    render(<InputBar onSubmit={handleSubmit} />);

    const textarea = screen.getByRole("textbox");

    fireEvent.change(textarea, { target: { value: "  hello world  " } });

    fireEvent.keyDown(textarea, {
      key: "Enter",
      code: "Enter",
      charCode: 13,
    });

    expect(handleSubmit).toHaveBeenCalledTimes(1);
    expect(handleSubmit).toHaveBeenCalledWith("hello world");

    expect((textarea as HTMLTextAreaElement).value).toBe("");
  });

  it("does not submit when value is empty or whitespace only", () => {
    const handleSubmit = vi.fn();

    render(<InputBar onSubmit={handleSubmit} />);

    const textarea = screen.getByRole("textbox");

    fireEvent.change(textarea, { target: { value: "   " } });
    fireEvent.keyDown(textarea, {
      key: "Enter",
      code: "Enter",
      charCode: 13,
    });

    expect(handleSubmit).not.toHaveBeenCalled();
  });

  it("does not submit on Enter while streaming", () => {
    const handleSubmit = vi.fn();

    render(<InputBar onSubmit={handleSubmit} isStreaming />);

    const textarea = screen.getByRole("textbox");

    fireEvent.change(textarea, { target: { value: "hello" } });
    fireEvent.keyDown(textarea, {
      key: "Enter",
      code: "Enter",
      charCode: 13,
    });

    expect(handleSubmit).not.toHaveBeenCalled();
  });

  it("calls onAbort when Stop streaming button is clicked", () => {
    const handleAbort = vi.fn();

    render(<InputBar onSubmit={vi.fn()} isStreaming onAbort={handleAbort} />);

    const abortButton = screen.getByRole("button", {
      name: /stop streaming/i,
    });

    fireEvent.click(abortButton);

    expect(handleAbort).toHaveBeenCalledTimes(1);
  });

  it("still submits on Enter even when disabled prop is true (current behavior)", () => {
    const handleSubmit = vi.fn();

    render(<InputBar onSubmit={handleSubmit} disabled />);

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "hello" } });

    fireEvent.keyDown(textarea, {
      key: "Enter",
      code: "Enter",
      charCode: 13,
    });

    expect(handleSubmit).toHaveBeenCalledTimes(1);
    expect(handleSubmit).toHaveBeenCalledWith("hello");
  });

  it("can submit by clicking the Send button when enabled", () => {
    const handleSubmit = vi.fn();

    render(<InputBar onSubmit={handleSubmit} />);

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "click send" } });

    const sendButton = screen.getByRole("button", { name: /send/i });
    fireEvent.click(sendButton);

    expect(handleSubmit).toHaveBeenCalledTimes(1);
    expect(handleSubmit).toHaveBeenCalledWith("click send");
  });
});
