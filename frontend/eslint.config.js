import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import simpleImportSort from "eslint-plugin-simple-import-sort";
import tseslint from "typescript-eslint";
import { defineConfig } from "eslint/config";

/**
 * Remove every `// ...` line comment.
 * Keeps block comments like /* ... *\/
 */
const noLineCommentsRule = {
  meta: {
    type: "problem",
    docs: { description: "Disallow and auto-remove // line comments" },
    fixable: "code",
    schema: [],
    messages: { remove: "Line comments starting with // are not allowed. Removed." },
  },
  create(context) {
    const src = context.getSourceCode();
    return {
      Program() {
        const comments = src.getAllComments();
        for (const c of comments) {
          if (c.type !== "Line") continue;
          context.report({
            loc: c.loc,
            messageId: "remove",
            fix(fixer) {
              const t = src.text;
              const [s, e] = c.range;
              const lineStart = t.lastIndexOf("\n", s - 1) + 1;
              const before = t.slice(lineStart, s);
              const hasCode = /\S/.test(before);

              if (hasCode) {
                const codeEnd = before.replace(/\s+$/, "").length;
                return fixer.removeRange([lineStart + codeEnd, e]);
              }
              return fixer.removeRange([lineStart, e]);
            },
          });
        }
      },
    };
  },
};

export default defineConfig([
  {
    ignores: [
      "**/node_modules/**",
      "**/dist/**",
      "**/build/**",
      "**/coverage/**",
      "**/assets/**",
      "**/*.min.js",
    ],
  },
  {
    files: ["**/*.{ts,tsx,js,jsx}"],
    ignores: ["**/eslint.config.*"],
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        ecmaVersion: 2022,
        sourceType: "module",
        ecmaFeatures: { jsx: true },
        comment: true,
        loc: true,
        range: true,
        tokens: true,
      },
      globals: { ...globals.browser, ...globals.es2022 },
    },

    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs["recommended-latest"],
      reactRefresh.configs.vite,
    ],

    plugins: {
      internal: { rules: { "no-line-comments": noLineCommentsRule } },
      "simple-import-sort": simpleImportSort,
    },
    rules: {
      "internal/no-line-comments": "error",
      "@typescript-eslint/no-explicit-any": "off",
      "simple-import-sort/imports": [
        "error",
        {
          groups: [
            ["^react$", "^react-dom$"],
            ["^@?\\w"],
            ["^@/"],
            ["^\\.\\./", "^\\./"],
          ],
        },
      ],
      "simple-import-sort/exports": "error",
    },
  },
]);
