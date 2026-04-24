/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bg-primary': '#0A0C10',
        'bg-card': '#111318',
        'bg-elevated': '#1A1E26',
        'border': '#2A2E38',
        'accent-saffron': '#FF9933',
        'accent-green': '#138808',
        'accent-blue': '#1C4ED8',
        'accent-red': '#DC2626',
        'accent-amber': '#D97706',
        'text-primary': '#F1F5F9',
        'text-secondary': '#94A3B8',
        'text-muted': '#475569',
      },
      fontFamily: {
        'display': ['DM Serif Display', 'serif'],
        'body': ['Mukta', 'sans-serif'],
        'mono': ['IBM Plex Mono', 'monospace'],
      }
    },
  },
  plugins: [],
}