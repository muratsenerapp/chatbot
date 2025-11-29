import * as matchers from "@testing-library/jest-dom/matchers";
import { expect } from "vitest";
expect.extend(matchers);

type ESReadyState = 0 | 1 | 2;

class FakeEventSource extends EventTarget {
  static readonly CONNECTING: ESReadyState = 0;
  static readonly OPEN: ESReadyState = 1;
  static readonly CLOSED: ESReadyState = 2;

  readonly OPEN: ESReadyState = FakeEventSource.OPEN;

  url: string;
  withCredentials: boolean;
  readyState: ESReadyState = FakeEventSource.CONNECTING;

  onopen: ((this: EventSource, ev: Event) => any) | null = null;

  constructor(url: string | URL, init?: EventSourceInit) {
    super();
    this.url = typeof url === "string" ? url : url.toString();
    this.withCredentials = !!init?.withCredentials;
  }

  close(): void {
    if (this.readyState === FakeEventSource.CLOSED) return;
    this.readyState = FakeEventSource.CLOSED;
  }

  openNow(): void {
    this.readyState = this.OPEN;
    const ev = new Event("open");
    this.onopen?.call(this as unknown as EventSource, ev);
    this.dispatchEvent(ev);
  }

  emitBackendError(data?: any): void {
    const ev = new MessageEvent("backend-error", { data });
    this.dispatchEvent(ev);
  }
}

(globalThis as any).EventSource = FakeEventSource as unknown as {
  new (url: string | URL, eventSourceInitDict?: EventSourceInit): EventSource;
  prototype: EventSource;
};
