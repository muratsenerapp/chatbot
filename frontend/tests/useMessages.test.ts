import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { useMessages } from "@/hooks/useMessages";

vi.mock("@/lib/idGenerator", () => {
  let counter = 0;
  return {
    newId: () => `test-id-${++counter}`,
  };
});

describe("useMessages", () => {
  describe("initial state", () => {
    it("returns empty messages array initially", () => {
      const { result } = renderHook(() => useMessages());

      expect(result.current.messages).toEqual([]);
    });

    it("has null streamingAssistantId initially", () => {
      const { result } = renderHook(() => useMessages());

      expect(result.current.streamingAssistantId.current).toBeNull();
    });
  });

  describe("pushUserMessage", () => {
    it("adds a user message to messages array", () => {
      const { result } = renderHook(() => useMessages());

      act(() => {
        result.current.pushUserMessage("Hello");
      });

      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0].role).toBe("user");
      expect(result.current.messages[0].content).toBe("Hello");
    });

    it("returns the created message with correct structure", () => {
      const { result } = renderHook(() => useMessages());

      let returnedMessage: ReturnType<typeof result.current.pushUserMessage>;
      act(() => {
        returnedMessage = result.current.pushUserMessage("Test message");
      });

      expect(returnedMessage!).toBeDefined();
      expect(returnedMessage!.id).toBeDefined();
      expect(typeof returnedMessage!.id).toBe("string");
      expect(returnedMessage!.role).toBe("user");
      expect(returnedMessage!.content).toBe("Test message");
    });

    it("assigns unique id to each message", () => {
      const { result } = renderHook(() => useMessages());

      let msg1: ReturnType<typeof result.current.pushUserMessage>;
      let msg2: ReturnType<typeof result.current.pushUserMessage>;

      act(() => {
        msg1 = result.current.pushUserMessage("First");
      });

      act(() => {
        msg2 = result.current.pushUserMessage("Second");
      });

      expect(msg1!.id).not.toBe(msg2!.id);
    });

    it("appends multiple user messages in order", () => {
      const { result } = renderHook(() => useMessages());

      act(() => {
        result.current.pushUserMessage("First");
        result.current.pushUserMessage("Second");
        result.current.pushUserMessage("Third");
      });

      expect(result.current.messages).toHaveLength(3);
      expect(result.current.messages[0].content).toBe("First");
      expect(result.current.messages[1].content).toBe("Second");
      expect(result.current.messages[2].content).toBe("Third");
    });
  });

  describe("addAssistantMessage", () => {
    it("adds an assistant message to messages array", () => {
      const { result } = renderHook(() => useMessages());

      act(() => {
        result.current.addAssistantMessage("Hello from assistant");
      });

      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0].role).toBe("assistant");
      expect(result.current.messages[0].content).toBe("Hello from assistant");
    });

    it("returns the created assistant message", () => {
      const { result } = renderHook(() => useMessages());

      let returnedMessage: ReturnType<typeof result.current.addAssistantMessage>;
      act(() => {
        returnedMessage = result.current.addAssistantMessage("Response");
      });

      expect(returnedMessage!).toBeDefined();
      expect(returnedMessage!.id).toBeDefined();
      expect(returnedMessage!.role).toBe("assistant");
      expect(returnedMessage!.content).toBe("Response");
    });

    it("adds message without error flag by default", () => {
      const { result } = renderHook(() => useMessages());

      act(() => {
        result.current.addAssistantMessage("Normal response");
      });

      expect(result.current.messages[0].error).toBeUndefined();
    });

    it("adds message with error flag when error option is true", () => {
      const { result } = renderHook(() => useMessages());

      act(() => {
        result.current.addAssistantMessage("Something went wrong", {
          error: true,
        });
      });

      expect(result.current.messages[0].error).toBe(true);
      expect(result.current.messages[0].content).toBe("Something went wrong");
    });

    it("adds message without error flag when error option is false", () => {
      const { result } = renderHook(() => useMessages());

      act(() => {
        result.current.addAssistantMessage("Normal response", { error: false });
      });

      expect(result.current.messages[0].error).toBe(false);
    });
  });

  describe("createAssistantDraft", () => {
    it("creates an empty assistant message draft", () => {
      const { result } = renderHook(() => useMessages());

      act(() => {
        result.current.createAssistantDraft();
      });

      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0].role).toBe("assistant");
      expect(result.current.messages[0].content).toBe("");
    });

    it("returns the created draft message", () => {
      const { result } = renderHook(() => useMessages());

      let draft: ReturnType<typeof result.current.createAssistantDraft>;
      act(() => {
        draft = result.current.createAssistantDraft();
      });

      expect(draft!).toBeDefined();
      expect(draft!.id).toBeDefined();
      expect(draft!.role).toBe("assistant");
      expect(draft!.content).toBe("");
    });

    it("sets streamingAssistantId to the draft id", () => {
      const { result } = renderHook(() => useMessages());

      let draft: ReturnType<typeof result.current.createAssistantDraft>;
      act(() => {
        draft = result.current.createAssistantDraft();
      });

      expect(result.current.streamingAssistantId.current).toBe(draft!.id);
    });

    it("updates streamingAssistantId when creating new draft", () => {
      const { result } = renderHook(() => useMessages());

      let firstDraft: ReturnType<typeof result.current.createAssistantDraft>;
      let secondDraft: ReturnType<typeof result.current.createAssistantDraft>;

      act(() => {
        firstDraft = result.current.createAssistantDraft();
      });

      act(() => {
        secondDraft = result.current.createAssistantDraft();
      });

      expect(result.current.streamingAssistantId.current).toBe(secondDraft!.id);
      expect(result.current.streamingAssistantId.current).not.toBe(
        firstDraft!.id,
      );
    });
  });

  describe("appendToAssistant", () => {
    it("appends token to the streaming assistant message", () => {
      const { result } = renderHook(() => useMessages());

      act(() => {
        result.current.createAssistantDraft();
      });

      act(() => {
        result.current.appendToAssistant("Hello");
      });

      expect(result.current.messages[0].content).toBe("Hello");
    });

    it("appends multiple tokens sequentially", () => {
      const { result } = renderHook(() => useMessages());

      act(() => {
        result.current.createAssistantDraft();
      });

      act(() => {
        result.current.appendToAssistant("Hello ");
        result.current.appendToAssistant("World");
        result.current.appendToAssistant("!");
      });

      expect(result.current.messages[0].content).toBe("Hello World!");
    });

    it("ignores empty string tokens", () => {
      const { result } = renderHook(() => useMessages());

      act(() => {
        result.current.createAssistantDraft();
      });

      act(() => {
        result.current.appendToAssistant("First");
        result.current.appendToAssistant("");
        result.current.appendToAssistant("Second");
      });

      expect(result.current.messages[0].content).toBe("FirstSecond");
    });

    it("does nothing when streamingAssistantId is null", () => {
      const { result } = renderHook(() => useMessages());

      act(() => {
        result.current.appendToAssistant("Orphan token");
      });

      expect(result.current.messages).toHaveLength(0);
    });

    it("only appends to the correct streaming message", () => {
      const { result } = renderHook(() => useMessages());

      act(() => {
        result.current.addAssistantMessage("First assistant message");
      });

      act(() => {
        result.current.createAssistantDraft();
      });

      act(() => {
        result.current.appendToAssistant("Streaming content");
      });

      expect(result.current.messages[0].content).toBe("First assistant message");
      expect(result.current.messages[1].content).toBe("Streaming content");
    });

    it("handles special characters in tokens", () => {
      const { result } = renderHook(() => useMessages());

      act(() => {
        result.current.createAssistantDraft();
      });

      act(() => {
        result.current.appendToAssistant("<div>");
        result.current.appendToAssistant("&amp;");
        result.current.appendToAssistant("</div>");
      });

      expect(result.current.messages[0].content).toBe("<div>&amp;</div>");
    });

    it("handles unicode characters in tokens", () => {
      const { result } = renderHook(() => useMessages());

      act(() => {
        result.current.createAssistantDraft();
      });

      act(() => {
        result.current.appendToAssistant("Merhaba ");
        result.current.appendToAssistant("dünya ");
        result.current.appendToAssistant("🌍");
      });

      expect(result.current.messages[0].content).toBe("Merhaba dünya 🌍");
    });
  });

  describe("markAssistantError", () => {
    it("marks the streaming assistant message as an error", () => {
      const { result } = renderHook(() => useMessages());

      act(() => {
        result.current.createAssistantDraft();
      });

      act(() => {
        result.current.appendToAssistant("Partial response");
      });

      act(() => {
        result.current.markAssistantError("Custom error message");
      });

      expect(result.current.messages[0].error).toBe(true);
      expect(result.current.messages[0].content).toBe("Custom error message");
    });

    it("uses default error message when none provided", () => {
      const { result } = renderHook(() => useMessages());

      act(() => {
        result.current.createAssistantDraft();
      });

      act(() => {
        result.current.markAssistantError();
      });

      expect(result.current.messages[0].error).toBe(true);
      expect(result.current.messages[0].content).toBe(
        "Sorry, something went wrong.",
      );
    });

    it("does nothing when streamingAssistantId is null", () => {
      const { result } = renderHook(() => useMessages());

      act(() => {
        result.current.addAssistantMessage("Regular message");
      });

      act(() => {
        result.current.markAssistantError("Error");
      });

      expect(result.current.messages[0].error).toBeUndefined();
      expect(result.current.messages[0].content).toBe("Regular message");
    });

    it("only marks the correct streaming message as error", () => {
      const { result } = renderHook(() => useMessages());

      act(() => {
        result.current.addAssistantMessage("First message");
      });

      act(() => {
        result.current.createAssistantDraft();
      });

      act(() => {
        result.current.markAssistantError("Error occurred");
      });

      expect(result.current.messages[0].error).toBeUndefined();
      expect(result.current.messages[0].content).toBe("First message");
      expect(result.current.messages[1].error).toBe(true);
      expect(result.current.messages[1].content).toBe("Error occurred");
    });
  });

  describe("mixed message operations", () => {
    it("handles interleaved user and assistant messages", () => {
      const { result } = renderHook(() => useMessages());

      act(() => {
        result.current.pushUserMessage("User question");
      });

      act(() => {
        result.current.createAssistantDraft();
      });

      act(() => {
        result.current.appendToAssistant("Assistant answer");
      });

      act(() => {
        result.current.pushUserMessage("Follow up");
      });

      act(() => {
        result.current.addAssistantMessage("Another response");
      });

      expect(result.current.messages).toHaveLength(4);
      expect(result.current.messages[0].role).toBe("user");
      expect(result.current.messages[0].content).toBe("User question");
      expect(result.current.messages[1].role).toBe("assistant");
      expect(result.current.messages[1].content).toBe("Assistant answer");
      expect(result.current.messages[2].role).toBe("user");
      expect(result.current.messages[2].content).toBe("Follow up");
      expect(result.current.messages[3].role).toBe("assistant");
      expect(result.current.messages[3].content).toBe("Another response");
    });
  });
});
