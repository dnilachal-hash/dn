import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef5fb",
          100: "#d9e7f3",
          500: "#1f4e79",
          600: "#1a4267",
          700: "#143655",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
