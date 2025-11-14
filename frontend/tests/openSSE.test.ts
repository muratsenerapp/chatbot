import { describe, it, beforeEach, afterEach, expect, vi } from "vitest";
import { openSSE } from "@lib/sse";

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
  if (instances.length === 0)
    throw new Error("No EventSource instance was created");
  return instances[0] as any;
}

describe("openSSE event semantics", () => {
  it("builds URL with params while skipping null/undefined values", () => {
    openSSE("/sse", {
      params: {
        a: "1",
        b: null,
        c: undefined,
      },
      debug: true,
    });

    const es: any = getES();
    const url = new URL(es.url, window.location.origin);

    expect(url.searchParams.get("a")).toBe("1");
    expect(url.searchParams.has("b")).toBe(false);
    expect(url.searchParams.has("c")).toBe(false);
  });

  it("delivers token chunks to onToken and respects manual close", () => {
    const chunks: string[] = [];

    const { close } = openSSE("/sse", {
      debug: true,
      onToken: (chunk) => {
        chunks.push(chunk);
      },
    });

    const es: any = getES();

    es.dispatchEvent(new MessageEvent("token", { data: "Hel" }));
    es.dispatchEvent(new MessageEvent("token", { data: "lo" }));

    expect(chunks).toEqual(["Hel", "lo"]);

    close();

    es.dispatchEvent(new MessageEvent("token", { data: " ignored" }));
    expect(chunks).toEqual(["Hel", "lo"]);
  });

  it("parses JSON metrics in done event and closes the stream", () => {
    let received: any = null;

    openSSE("/sse", {
      debug: true,
      onDone: (metrics) => {
        received = metrics;
      },
    });

    const es: any = getES();
    const closeSpy = vi.spyOn(es, "close");

    const metrics = {
      session_id: "sess-1",
      chars: 42,
      elapsed_ms: 1234,
    };

    es.dispatchEvent(
      new MessageEvent("done", {
        data: JSON.stringify(metrics),
      }),
    );

    expect(received).toEqual(metrics);
    expect(closeSpy).toHaveBeenCalledTimes(1);
  });

  it("passes null to onDone when done payload is not valid JSON", () => {
    let received: any = "initial";

    openSSE("/sse", {
      debug: true,
      onDone: (metrics) => {
        received = metrics;
      },
    });

    const es: any = getES();

    es.dispatchEvent(
      new MessageEvent("done", {
        data: "not-a-json",
      }),
    );

    expect(received).toBeNull();
  });

  it("invokes onNetworkError and onClose on transport error", () => {
    let networkErrors = 0;
    let closeCalls = 0;

    openSSE("/sse", {
      debug: true,
      onNetworkError: () => {
        networkErrors += 1;
      },
      onClose: () => {
        closeCalls += 1;
      },
    });

    const es: any = getES();
    const closeSpy = vi.spyOn(es, "close");

    const errorEvent = new Event("error");

    if (typeof es.onerror === "function") {
      es.onerror(errorEvent);
    } else {
      es.dispatchEvent(errorEvent);
    }

    expect(networkErrors).toBe(1);
    expect(closeCalls).toBe(1);
    expect(closeSpy).toHaveBeenCalledTimes(1);
  });

  it("ignores network errors after manual close (debug branch too)", () => {
    let networkErrors = 0;
    let closeCalls = 0;

    const { close } = openSSE("/sse", {
      debug: true,
      onNetworkError: () => {
        networkErrors += 1;
      },
      onClose: () => {
        closeCalls += 1;
      },
    });

    const es: any = getES();
    const closeSpy = vi.spyOn(es, "close");

    close();

    const errorEvent = new Event("error");
    if (typeof es.onerror === "function") {
      es.onerror(errorEvent);
    } else {
      es.dispatchEvent(errorEvent);
    }

    expect(closeCalls).toBe(1);
    expect(closeSpy).toHaveBeenCalledTimes(1);

    expect(networkErrors).toBe(0);
  });
});
