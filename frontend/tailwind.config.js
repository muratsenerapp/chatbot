/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      height: {
        "main-content": "calc(100dvh - var(--header-height))",
      },
    },
  },
  plugins: [],
};
