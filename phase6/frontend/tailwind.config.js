/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        zomato: {
          red: '#E23744',
          dark: '#CB202D',
          light: '#FFF5F6',
        },
      },
    },
  },
  plugins: [],
};

