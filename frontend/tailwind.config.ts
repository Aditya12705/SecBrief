import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "slide-in-from-top": {
          "0%": { transform: "translateY(-1rem)" },
          "100%": { transform: "translateY(0)" },
        },
        "slide-in-from-bottom": {
          "0%": { transform: "translateY(1rem)" },
          "100%": { transform: "translateY(0)" },
        },
      },
      animation: {
        "in": "fade-in 0.5s ease-out forwards",
      },
      colors: {
        ve: {
          bg: "#0b0f1a",
          card: "#121829",
          accent: "#6ee7b7",
          warn: "#fbbf24",
          danger: "#f87171",
        },
      },
    },
  },
  plugins: [],
};
export default config;
