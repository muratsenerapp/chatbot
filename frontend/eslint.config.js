import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";
import { defineConfig, globalIgnores } from "eslint/config";

const noLineCommentsRule = {
  meta: {
    type: "problem",
    fixable: "code",
    schema: [],
    messages: {
      remove: "Line comments starting with // are not allowed. Removed.",
    },
  },
  create(context) {
    const src = context.sourceCode;
    return {
      Program() {
        for (const c of src.getAllComments()) {
          if (c.type === "Line") {
            context.report({
              loc: c.loc,
              messageId: "remove",
              fix(fixer) {
                const text = src.text;
                let [start, end] = c.range;
                while (start > 0 && text[start - 1] !== "\n") {
                  if (/\s/.test(text[start - 1])) start--;
                  else break;
                }
                if (text[end] === "\r") end++;
                if (text[end] === "\n") end++;
                return fixer.removeRange([start, end]);
              },
            });
          }
        }
      },
    };
  },
};

export default defineConfig([
  globalIgnores(["dist", "node_modules"]),
  {
    files: ["**/*.{ts,tsx,js,jsx}"],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs["recommended-latest"],
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: { ...globals.browser, ...globals.es2022 },
    },
    plugins: {
      internal: { rules: { "no-line-comments": noLineCommentsRule } },
    },
    rules: { "internal/no-line-comments": "error" },
  },
]);
