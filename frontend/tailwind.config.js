/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: '#FAFAF7',
        surface: '#FFFFFF',
        ink: '#16181B',
        muted: '#5B6168',
        line: '#E4E4DF',
        accent: '#2457D6',
        hit: '#0F6CBD',
        miss: '#C2410C',
        cost: '#7C3AED',
        warn: '#8A6100'
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['Source Serif 4', 'Georgia', 'serif'],
      }
    },
  },
  plugins: [],
}
