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

export function openSSE(url: string, opts: OpenSSEOptions = {}) {
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
      if (v !== undefined && v !== null) fullUrl.searchParams.set(k, String(v));
    }
  }

  const es = new EventSource(fullUrl.toString());
  let manuallyClosed = false;

  function close() {
    if (!manuallyClosed) {
      manuallyClosed = true;
      if (debug) console.debug("[SSE] close()");
      es.close();
      onClose?.();
    }
  }

  es.onopen = () => {
    if (debug) console.debug("[SSE] open:", fullUrl.toString());
    onOpen?.();
  };

  // Server-sent "error" event
  es.addEventListener("error", (ev) => {
    const me = ev as MessageEvent;
    if (debug) console.debug("[SSE] server error event:", me.data);
    const msg = typeof me.data === "string" ? me.data : "Server error";
    onServerErrorEvent?.(msg);
    close(); // stop reconnects
  });

  es.addEventListener("token", (ev) => {
    const me = ev as MessageEvent;
    if (debug) console.debug("[SSE] token:", me.data);
    if (typeof me.data === "string") onToken?.(me.data);
  });

  es.addEventListener("done", (ev) => {
    const me = ev as MessageEvent;
    if (debug) console.debug("[SSE] done:", me.data);
    try {
      onDone?.(JSON.parse(me.data));
    } catch {
      onDone?.(null);
    }
    close(); // close on normal end
  });

  // Transport errors (disconnect, CORS, etc.)
  es.onerror = (ev) => {
    // Ignore if we already closed intentionally or ES is CLOSED (2)
    const rs = es.readyState;
    if (manuallyClosed || rs === 2) {
      if (debug) console.debug("[SSE] network error ignored after close");
      return;
    }
    if (debug) console.debug("[SSE] network error:", ev, "readyState:", rs);
    onNetworkError?.(ev);
  };

  return { es, close };
}
