import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
import tsconfigPaths from "vite-tsconfig-paths";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [
    react(),
    tsconfigPaths({ projects: ["./tsconfig.app.json", "./tsconfig.json"] }),
  ],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
      "@components": fileURLToPath(
        new URL("./src/components", import.meta.url),
      ),
      "@lib": fileURLToPath(new URL("./src/lib", import.meta.url)),
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    environmentOptions: { jsdom: { url: "http://localhost/" } },
    setupFiles: "./tests/setup.ts",
    include: ["tests/**/*.{test,spec}.{ts,tsx}"],

    coverage: {
      enabled: true,
      provider: "v8",
      reporter: ["text", "lcov", "html"],
      reportsDirectory: "./coverage",
      thresholds: {
        lines: 70,
        functions: 70,
        branches: 70,
        statements: 70,
      },
    },
  },
});
