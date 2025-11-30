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
  } = opts;

  const fullUrl = new URL(url, window.location.origin);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null) {
        fullUrl.searchParams.set(key, String(value));
      }
    }
  }

  const eventSource = new EventSource(fullUrl.toString());

  let didClose = false;
  let manuallyClosed = false;

  let onBackendErrorRef: ((ev: Event) => void) | null = null;
  let onTokenRef: ((ev: Event) => void) | null = null;
  let onDoneRef: ((ev: Event) => void) | null = null;

  function close(ev?: Event) {
    if (didClose) return;
    didClose = true;

    if (manuallyClosed) {
      if (onBackendErrorRef) {
        eventSource.removeEventListener("backend-error", onBackendErrorRef);
      }
      if (onTokenRef) {
        eventSource.removeEventListener("token", onTokenRef);
      }
      if (onDoneRef) {
        eventSource.removeEventListener("done", onDoneRef);
      }
      eventSource.onopen = null as any;
      eventSource.onerror = null as any;
      eventSource.onmessage = null as any;
    }

    eventSource.close();
    onClose?.(ev);
  }

  onBackendErrorRef = (ev: Event) => {
    if (manuallyClosed) return;
    const messageEvent = ev as MessageEvent;
    const message =
      typeof messageEvent.data === "string"
        ? messageEvent.data
        : "Server error";
    onServerErrorEvent?.(message);
    close(ev);
  };

  onTokenRef = (ev: Event) => {
    if (manuallyClosed) return;
    const messageEvent = ev as MessageEvent;
    if (typeof messageEvent.data === "string") {
      onToken?.(messageEvent.data);
    }
  };

  onDoneRef = (ev: Event) => {
    if (manuallyClosed) return;
    const messageEvent = ev as MessageEvent;
    try {
      onDone?.(JSON.parse(messageEvent.data));
    } catch {
      onDone?.(null);
    }
    close(ev);
  };

  eventSource.addEventListener("backend-error", onBackendErrorRef);
  eventSource.addEventListener("token", onTokenRef);
  eventSource.addEventListener("done", onDoneRef);

  eventSource.onopen = () => {
    onOpen?.();
  };

  eventSource.onerror = (ev) => {
    const readyState = eventSource.readyState;
    if (manuallyClosed || readyState === 2) {
      return;
    }
    onNetworkError?.(ev);
    close(ev);
  };

  const publicClose = (ev?: Event) => {
    manuallyClosed = true;
    close(ev);
  };

  return { eventSource, close: publicClose };
}

/** Public return type of {@link openSSE}. */
export type OpenSSEReturn = ReturnType<typeof openSSE>;
