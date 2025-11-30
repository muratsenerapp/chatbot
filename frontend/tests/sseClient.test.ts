import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { openSSE } from "@/lib";

const instances: EventSource[] = [];
const BaseES = globalThis.EventSource as any;

beforeEach(() => {
  instances.length = 0;

  (globalThis as any).EventSource = class extends (BaseES as any) {
    url: string;

    constructor(url: string | URL, init?: EventSourceInit) {
      super(url, init);
      this.url = typeof url === "string" ? url : url.toString();
      instances.push(this as unknown as EventSource);
    }
  } as any;
});

afterEach(() => {
  (globalThis as any).EventSource = BaseES;
  vi.restoreAllMocks();
});

function getES(): any {
  if (instances.length === 0) {
    throw new Error("No EventSource instance was created");
  }
  return instances[0] as any;
}

describe("openSSE", () => {
  describe("URL building", () => {
    it("builds URL with params while skipping null/undefined values", () => {
      openSSE("/sse", {
        params: {
          a: "1",
          b: null,
          c: undefined,
        },
      });

      const eventSource: any = getES();
      const url = new URL(eventSource.url, window.location.origin);

      expect(url.searchParams.get("a")).toBe("1");
      expect(url.searchParams.has("b")).toBe(false);
      expect(url.searchParams.has("c")).toBe(false);
    });
  });

  describe("connection lifecycle", () => {
    it("invokes onOpen callback when connection opens", () => {
      let openCalls = 0;

      openSSE("/sse", {
        onOpen: () => {
          openCalls += 1;
        },
      });

      const eventSource: any = getES();
      eventSource.openNow();

      expect(openCalls).toBe(1);
    });

    it("closes the EventSource and invokes onClose", () => {
      let closeCalls = 0;

      const { close } = openSSE("/sse", {
        onClose: () => {
          closeCalls += 1;
        },
      });

      const eventSource: any = getES();
      const closeSpy = vi.spyOn(eventSource, "close");

      close();

      expect(closeCalls).toBe(1);
      expect(closeSpy).toHaveBeenCalledTimes(1);
    });

    it("is idempotent - multiple close calls only trigger once", () => {
      let closeCalls = 0;

      const { close } = openSSE("/sse", {
        onClose: () => {
          closeCalls += 1;
        },
      });

      close();
      close();
      close();

      expect(closeCalls).toBe(1);
    });
  });

  describe("token streaming", () => {
    it("delivers token chunks to onToken callback", () => {
      const chunks: string[] = [];

      openSSE("/sse", {
        onToken: (chunk) => {
          chunks.push(chunk);
        },
      });

      const eventSource: any = getES();

      eventSource.dispatchEvent(new MessageEvent("token", { data: "Hello " }));
      eventSource.dispatchEvent(new MessageEvent("token", { data: "world!" }));

      expect(chunks).toEqual(["Hello ", "world!"]);
    });

    it("ignores tokens after manual close", () => {
      const chunks: string[] = [];

      const { close } = openSSE("/sse", {
        onToken: (chunk) => {
          chunks.push(chunk);
        },
      });

      const eventSource: any = getES();

      eventSource.dispatchEvent(new MessageEvent("token", { data: "before" }));
      close();
      eventSource.dispatchEvent(new MessageEvent("token", { data: "after" }));

      expect(chunks).toEqual(["before"]);
    });
  });

  describe("done event", () => {
    it("parses JSON metrics and closes the stream", () => {
      let received: any = null;

      openSSE("/sse", {
        onDone: (metrics) => {
          received = metrics;
        },
      });

      const eventSource: any = getES();
      const closeSpy = vi.spyOn(eventSource, "close");

      const metrics = {
        session_id: "sess-1",
        chars: 42,
        elapsed_ms: 1234,
      };

      eventSource.dispatchEvent(
        new MessageEvent("done", { data: JSON.stringify(metrics) }),
      );

      expect(received).toEqual(metrics);
      expect(closeSpy).toHaveBeenCalledTimes(1);
    });

    it("passes null to onDone when payload is not valid JSON", () => {
      let received: any = "initial";

      openSSE("/sse", {
        onDone: (metrics) => {
          received = metrics;
        },
      });

      const eventSource: any = getES();

      eventSource.dispatchEvent(
        new MessageEvent("done", { data: "not-a-json" }),
      );

      expect(received).toBeNull();
    });

    it("ignores done events after manual close", () => {
      let doneCalls = 0;

      const { close } = openSSE("/sse", {
        onDone: () => {
          doneCalls += 1;
        },
      });

      const eventSource: any = getES();

      close();
      eventSource.dispatchEvent(
        new MessageEvent("done", { data: JSON.stringify({}) }),
      );

      expect(doneCalls).toBe(0);
    });
  });

  describe("backend error handling", () => {
    it("invokes onServerErrorEvent with error message", () => {
      const serverErrors: string[] = [];
      let closeCalls = 0;

      openSSE("/sse", {
        onServerErrorEvent: (msg) => {
          serverErrors.push(msg);
        },
        onClose: () => {
          closeCalls += 1;
        },
      });

      const eventSource: any = getES();
      const closeSpy = vi.spyOn(eventSource, "close");

      eventSource.dispatchEvent(
        new MessageEvent("backend-error", { data: "Rate limit exceeded" }),
      );

      expect(serverErrors).toEqual(["Rate limit exceeded"]);
      expect(closeCalls).toBe(1);
      expect(closeSpy).toHaveBeenCalledTimes(1);
    });

    it("uses default message when data is not a string", () => {
      const serverErrors: string[] = [];

      openSSE("/sse", {
        onServerErrorEvent: (msg) => {
          serverErrors.push(msg);
        },
      });

      const eventSource: any = getES();

      eventSource.dispatchEvent(
        new MessageEvent("backend-error", { data: null }),
      );

      expect(serverErrors).toEqual(["Server error"]);
    });

    it("ignores backend-error events after manual close", () => {
      const serverErrors: string[] = [];
      let closeCalls = 0;

      const { close } = openSSE("/sse", {
        onServerErrorEvent: (msg) => {
          serverErrors.push(msg);
        },
        onClose: () => {
          closeCalls += 1;
        },
      });

      close();

      const eventSource: any = getES();
      eventSource.dispatchEvent(
        new MessageEvent("backend-error", { data: "Should be ignored" }),
      );

      expect(serverErrors).toEqual([]);
      expect(closeCalls).toBe(1);
    });
  });

  describe("network error handling", () => {
    it("invokes onNetworkError and onClose on transport error", () => {
      let networkErrors = 0;
      let closeCalls = 0;

      openSSE("/sse", {
        onNetworkError: () => {
          networkErrors += 1;
        },
        onClose: () => {
          closeCalls += 1;
        },
      });

      const eventSource: any = getES();
      const closeSpy = vi.spyOn(eventSource, "close");

      if (typeof eventSource.onerror === "function") {
        eventSource.onerror(new Event("error"));
      }

      expect(networkErrors).toBe(1);
      expect(closeCalls).toBe(1);
      expect(closeSpy).toHaveBeenCalledTimes(1);
    });

    it("ignores network errors after manual close", () => {
      let networkErrors = 0;
      let closeCalls = 0;

      const { close } = openSSE("/sse", {
        onNetworkError: () => {
          networkErrors += 1;
        },
        onClose: () => {
          closeCalls += 1;
        },
      });

      const eventSource: any = getES();

      close();

      if (typeof eventSource.onerror === "function") {
        eventSource.onerror(new Event("error"));
      }

      expect(networkErrors).toBe(0);
      expect(closeCalls).toBe(1);
    });

    it("ignores network errors when readyState is CLOSED (2)", () => {
      let networkErrors = 0;
      let closeCalls = 0;

      openSSE("/sse", {
        onNetworkError: () => {
          networkErrors += 1;
        },
        onClose: () => {
          closeCalls += 1;
        },
      });

      const eventSource: any = getES();
      eventSource.readyState = 2;

      if (typeof eventSource.onerror === "function") {
        eventSource.onerror(new Event("error"));
      }

      expect(networkErrors).toBe(0);
      expect(closeCalls).toBe(0);
    });
  });
});
