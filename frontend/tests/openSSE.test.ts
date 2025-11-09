import { describe, it, beforeEach, afterEach, expect, vi } from "vitest";
import { openSSE } from "@lib/sse";

const instances: EventSource[] = [];
const BaseES = globalThis.EventSource as any;

beforeEach(() => {
  instances.length = 0;
  (globalThis as any).EventSource = class extends (BaseES as any) {
    constructor(url: string | URL, init?: EventSourceInit) {
      super(url, init);
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

describe("openSSE close semantics", () => {
  it("is idempotent when closed manually", () => {
    let onCloseCalls = 0;
    let serverErrorCalls = 0;

    const sse = openSSE("/sse", {
      onClose: () => {
        onCloseCalls += 1;
      },
      onServerErrorEvent: () => {
        serverErrorCalls += 1;
      },
    });

    const es = getES();
    const closeSpy = vi.spyOn(es, "close");

    if (typeof es.openNow === "function") es.openNow();

    sse.close();
    sse.close();

    expect(closeSpy).toHaveBeenCalledTimes(1);
    expect(onCloseCalls).toBe(1);

    if (typeof es.emitBackendError === "function") {
      es.emitBackendError("after-close-1");
      es.emitBackendError("after-close-2");
    } else {
      es.dispatchEvent(
        new MessageEvent("backend-error", { data: "after-close-1" }),
      );
      es.dispatchEvent(
        new MessageEvent("backend-error", { data: "after-close-2" }),
      );
    }

    expect(serverErrorCalls).toBe(0);
  });

  it("remains idempotent when server error events fire repeatedly", () => {
    let onCloseCalls = 0;
    let serverErrorCalls = 0;

    openSSE("/sse", {
      onClose: () => {
        onCloseCalls += 1;
      },
      onServerErrorEvent: () => {
        serverErrorCalls += 1;
      },
    });

    const es = getES();
    const closeSpy = vi.spyOn(es, "close");

    if (typeof es.emitBackendError === "function") {
      es.emitBackendError("e1");
      es.emitBackendError("e2");
    } else {
      es.dispatchEvent(new MessageEvent("backend-error", { data: "e1" }));
      es.dispatchEvent(new MessageEvent("backend-error", { data: "e2" }));
    }

    expect(closeSpy).toHaveBeenCalledTimes(1);
    expect(onCloseCalls).toBe(1);
    expect(serverErrorCalls).toBe(2);
  });
});
