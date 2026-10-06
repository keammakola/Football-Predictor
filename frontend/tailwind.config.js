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
        muted: '#566174',
        line: '#D1D5DB', // slightly darker for sharp lines
        accent: '#2563EB', // crisp blue
        cost: '#B91C1C', // readable red for simulated losses
      },
      fontFamily: {
        sans: ['Space Grotesk', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
