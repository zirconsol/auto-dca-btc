/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["'Inter'", "sans-serif"],
      },
      colors: {
        ink: {
          50: "#111827",
          100: "#1f2937",
          900: "#0b0f17",
        },
        accent: {
          50: "#fff4e5",
          100: "#ffe8cc",
          500: "#f7931a",
          600: "#d97904",
          700: "#b85f05",
        },
      },
    },
  },
  plugins: [],
};
