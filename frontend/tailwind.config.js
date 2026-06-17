/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        pepper: "#2b2b2b",
        salt: "#ffffff",
        ash: "#d4d4d4",
        smoke: "#b3b3b3",
        paper: "#f7f7f7",
      },
      boxShadow: {
        soft: "0 18px 44px rgba(43,43,43,0.08)",
      },
    },
  },
  plugins: [],
};
