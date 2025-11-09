import type { MutableRefObject } from "react";

export function closeAndClear(ref: MutableRefObject<(() => void) | null>) {
  if (ref.current) {
    const closer = ref.current;
    ref.current = null;
    closer();
  }
}
