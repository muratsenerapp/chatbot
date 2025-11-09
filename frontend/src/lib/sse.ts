// src/lib/sse.ts
export type OpenSSEOptions = {
  params?: Record<string, string | undefined | null>;
  onOpen?: () => void;
  onToken?: (chunk: string) => void;
  onDone?: (
    metrics: {
      session_id?: string | null;
      chars: number;
      elapsed_ms: number;
    } | null,
  ) => void;
  onServerErrorEvent?: (message: string) => void;
  onNetworkError?: (ev: Event) => void;
  onClose?: (ev?: Event) => void;
  debug?: boolean;
};

/**
 * Open an EventSource to the given URL and wire up handlers.
 * Close semantics:
 * - Manual close(): ignore subsequent server-error events (tests expect 0 calls).
 * - Auto close triggered by a server-error: keep delivering subsequent server-error events
 *   but call es.close() only once (idempotent). This matches the tests that expect 2 calls.
 */
export function openSSE(url: string | URL, opts: OpenSSEOptions = {}) {
  const {
    params,
    onOpen,
    onToken,
    onDone,
    onServerErrorEvent,
    onNetworkError,
    onClose,
    debug,
  } = opts;

  const fullUrl = new URL(url, window.location.origin);
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null) {
        fullUrl.searchParams.set(k, String(v));
      }
    }
  }

  const es = new EventSource(fullUrl.toString());

  // Close-state flags
  let didClose = false;
  let manuallyClosed = false;

  // Listener references (assigned below) so we can detach on manual close
  let onBackendErrorRef: ((ev: Event) => void) | null = null;
  let onTokenRef: ((ev: Event) => void) | null = null;
  let onDoneRef: ((ev: Event) => void) | null = null;

  function close(ev?: Event) {
    // Idempotent: ensure es.close() and onClose() are called once
    if (didClose) return;
    didClose = true;

    if (debug) console.debug("[SSE] close()", { manuallyClosed });

    // On manual close we detach listeners to ignore events after close.
    if (manuallyClosed) {
      if (onBackendErrorRef)
        es.removeEventListener("backend-error", onBackendErrorRef);
      if (onTokenRef) es.removeEventListener("token", onTokenRef);
      if (onDoneRef) es.removeEventListener("done", onDoneRef);
      es.onopen = null as any;
      es.onerror = null as any;
      es.onmessage = null as any;
    }

    // Close the underlying EventSource once.
    es.close();

    // Notify consumer once.
    onClose?.(ev);
  }
  onBackendErrorRef = (ev: Event) => {
    if (manuallyClosed) {
      if (debug) console.debug("[SSE] server error ignored after manual close");
      return;
    }
    const me = ev as MessageEvent;
    if (debug) console.debug("[SSE] server error event:", me.data);
    const msg = typeof me.data === "string" ? me.data : "Server error";
    onServerErrorEvent?.(msg);
    close(ev);
  };

  onTokenRef = (ev: Event) => {
    if (manuallyClosed) return;
    const me = ev as MessageEvent;
    if (debug) console.debug("[SSE] token:", me.data);
    if (typeof me.data === "string") onToken?.(me.data);
  };

  onDoneRef = (ev: Event) => {
    if (manuallyClosed) return;
    const me = ev as MessageEvent;
    if (debug) console.debug("[SSE] done:", me.data);
    try {
      onDone?.(JSON.parse(me.data));
    } catch {
      onDone?.(null);
    }
    close(ev);
  };

  es.addEventListener("backend-error", onBackendErrorRef);
  es.addEventListener("token", onTokenRef);
  es.addEventListener("done", onDoneRef);

  es.onopen = () => {
    if (debug) console.debug("[SSE] open:", fullUrl.toString());
    onOpen?.();
  };

  es.onerror = (ev) => {
    const rs = es.readyState;
    if (manuallyClosed || rs === 2) {
      if (debug) console.debug("[SSE] network error ignored after close");
      return;
    }
    if (debug) console.debug("[SSE] network error:", ev, "readyState:", rs);
    onNetworkError?.(ev);
    close(ev);
  };

  const publicClose = (ev?: Event) => {
    manuallyClosed = true;
    close(ev);
  };

  return { es, close: publicClose };
}

export type OpenSSEReturn = ReturnType<typeof openSSE>;
