/**
 * Options for {@link openSSE}.
 *
 * @remarks Callbacks are optional; absent handlers are simply skipped.
 * @public
 */
export type OpenSSEOptions = {
  /** Querystring parameters appended to the URL. */
  params?: Record<string, string | undefined | null>;
  /** Called once the connection is opened. */
  onOpen?: () => void;
  /** Receives each streamed token chunk. */
  onToken?: (chunk: string) => void;
  /** Called at end with streaming metrics (or `null` on error). */
  onDone?: (
    metrics: {
      session_id?: string | null;
      chars: number;
      elapsed_ms: number;
    } | null,
  ) => void;
  /** Receives backend-emitted SSE error messages. */
  onServerErrorEvent?: (message: string) => void;
  /** Called when the browser reports a transport error. */
  onNetworkError?: (ev: Event) => void;
  /** Always called when the stream is closed. */
  onClose?: (ev?: Event) => void;
  /** Enables verbose console logs for diagnostics. */
  debug?: boolean;
};

/**
 * Open a browser `EventSource` to a chat stream and wire typed callbacks.
 *
 * @returns An object with the underlying `EventSource` and an idempotent `close()` helper.
 * @public
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

  let didClose = false;
  let manuallyClosed = false;

  let onBackendErrorRef: ((ev: Event) => void) | null = null;
  let onTokenRef: ((ev: Event) => void) | null = null;
  let onDoneRef: ((ev: Event) => void) | null = null;

  function close(ev?: Event) {
    if (didClose) return;
    didClose = true;

    if (debug) console.debug("[SSE] close()", { manuallyClosed });

    if (manuallyClosed) {
      if (onBackendErrorRef)
        es.removeEventListener("backend-error", onBackendErrorRef);
      if (onTokenRef) es.removeEventListener("token", onTokenRef);
      if (onDoneRef) es.removeEventListener("done", onDoneRef);
      es.onopen = null as any;
      es.onerror = null as any;
      es.onmessage = null as any;
    }

    es.close();

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

/** Public return type of {@link openSSE}. */
export type OpenSSEReturn = ReturnType<typeof openSSE>;
