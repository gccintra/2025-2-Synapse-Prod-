/** @type {import('tailwindcss').Config} */
import typography from "@tailwindcss/typography";

export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        rajdhani: ["Rajdhani", "sans-serif"],
        montserrat: ["Montserrat", "sans-serif"],
      },
      fontSize: {
        "64xl": "64px",
        "160xl": "160px",
      },
    },
  },
  plugins: [typography],
};
