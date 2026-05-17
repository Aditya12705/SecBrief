import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
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
