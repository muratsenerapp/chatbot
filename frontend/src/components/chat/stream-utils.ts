import type { MutableRefObject } from "react";

/**
 * Idempotently invoke and clear a closer stored in a `ref`.
 *
 * @param ref - Mutable ref that may hold a cleanup function.
 * @public
 */
export function closeAndClear(ref: MutableRefObject<(() => void) | null>) {
  if (ref.current) {
    const closer = ref.current;
    ref.current = null;
    closer();
  }
}
