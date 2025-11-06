export type Role = "user" | "assistant";

export type ChatMessage = {
  id: string;
  role: Role;
  content: string;
  /** If true, render with error styling */
  error?: boolean;
};
