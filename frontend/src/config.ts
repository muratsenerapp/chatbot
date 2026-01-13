/**
 * Application configuration loaded from environment variables.
 *
 * @remarks
 * Uses Vite's environment variable system. Variables must be prefixed with VITE_
 * to be exposed to the client. See `.env.example` for available variables.
 */

/** Base URL for API endpoints. Defaults to relative path for same-origin proxy. */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

/** Full URL for the chat streaming endpoint. */
export const CHAT_STREAM_URL = `${API_BASE_URL}/chat/stream`;

/**
 * Layout constants used across the application.
 *
 * @remarks
 * These values should match the CSS variables defined in index.css.
 */
export const LAYOUT = {
  /** Height of the application header in pixels. */
  HEADER_HEIGHT_PX: 64,
} as const;
