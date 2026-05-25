/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // ESG green palette — muted and professional, not lime-green
        esg: {
          50: "#f0faf4",
          100: "#dcf2e4",
          200: "#bbe5cc",
          300: "#8dd0ab",
          400: "#5ab485",
          500: "#389768",
          600: "#277a52",
          700: "#206143",
          800: "#1d4e37",
          900: "#19402f",
        },
        // Neutral slate for backgrounds and text
        surface: {
          0: "#ffffff",
          50: "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          300: "#cbd5e1",
          400: "#94a3b8",
          500: "#64748b",
          600: "#475569",
          700: "#334155",
          800: "#1e293b",
          900: "#0f172a",
        },
      },
      fontFamily: {
        sans: ["'IBM Plex Sans'", "system-ui", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
    },
  },
  plugins: [],
};
