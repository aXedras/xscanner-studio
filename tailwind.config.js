/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // Enable dark mode with class strategy
  theme: {
    extend: {
      colors: {
        // xApp Brand Colors
        brand: {
          gold: '#C4A053',
          'gold-light': '#D4B876',
          'gold-dark': '#9A7A3A',
          red: '#D32F2F',
          yellow: '#F9A825',
        },
        // Functional colors
        success: '#5CB85C',
        error: '#FF3B30',
        warning: '#F39C12',
        // Dark mode palette
        dark: {
          bg: '#1C1C1E',
          surface: '#2C2C2E',
          'surface-light': '#3A3A3C',
        },
      },
      animation: {
        'blob': 'blob 7s infinite',
      },
      keyframes: {
        blob: {
          '0%': {
            transform: 'translate(0px, 0px) scale(1)',
          },
          '33%': {
            transform: 'translate(30px, -50px) scale(1.1)',
          },
          '66%': {
            transform: 'translate(-20px, 20px) scale(0.9)',
          },
          '100%': {
            transform: 'translate(0px, 0px) scale(1)',
          },
        },
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
      },
    },
  },
  plugins: [],
}
