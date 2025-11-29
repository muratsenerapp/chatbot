import { describe, it } from "vitest";
import assert from "node:assert/strict";
import { closeAndClear } from "@/lib/stream-utils";

describe("closeAndClear", () => {
  it("invokes the closer once and clears the ref", () => {
    let calls = 0;
    const ref: { current: null | (() => void) } = {
      current: () => {
        calls += 1;
      },
    };

    closeAndClear(ref);

    assert.strictEqual(calls, 1);
    assert.strictEqual(ref.current, null);

    closeAndClear(ref);
    assert.strictEqual(calls, 1);
  });
});
