/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        idbi: { 50: '#eff6ff', 500: '#1d4ed8', 700: '#1e40af', 900: '#1e3a8a' },
      },
    },
  },
  plugins: [],
}
