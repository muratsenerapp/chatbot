/**
 * Generate a unique identifier.
 *
 * @remarks Uses `crypto.randomUUID()` when available, otherwise falls back
 * to a timestamp-based ID.
 * @returns A unique string identifier.
 * @public
 */
export function newId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return String(Date.now()) + Math.random().toString(16).slice(2);
}
