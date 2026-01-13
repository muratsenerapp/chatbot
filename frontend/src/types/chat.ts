/** Participant role in the conversation. */
export type Role = "user" | "assistant";

/**
 * Minimal chat message shape used across the UI.
 *
 * @public
 */
export type ChatMessage = {
  id: string;
  role: Role;
  content: string;
  /** If true, render with error styling. */
  error?: boolean;
};
