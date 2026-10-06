/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: '#F3F4F6', // light cool gray / thermal paper feel
        surface: '#FFFFFF', // pure white
        ink: '#111827', // near black
        muted: '#6B7280',
        line: '#D1D5DB', // slightly darker for sharp lines
        accent: '#2563EB', // crisp blue
        cost: '#DC2626', // sharp red for house margin
      },
      fontFamily: {
        sans: ['Space Grotesk', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
