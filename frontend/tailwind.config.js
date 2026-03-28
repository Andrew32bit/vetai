/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        tg: {
          blue: "#2AABEE",
          dark: "#1a1a2e",
          bg: "var(--tg-theme-bg-color, #ffffff)",
          text: "var(--tg-theme-text-color, #000000)",
          hint: "var(--tg-theme-hint-color, #999999)",
          button: "var(--tg-theme-button-color, #2AABEE)",
          "button-text": "var(--tg-theme-button-text-color, #ffffff)",
        },
      },
    },
  },
  plugins: [],
};