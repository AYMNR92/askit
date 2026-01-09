/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // On ajoute des animations douces comme sur Lovable
      animation: {
        'enter': 'enter 0.3s ease-out forwards',
        'leave': 'leave 0.2s ease-in forwards',
      },
      keyframes: {
        enter: {
          '0%': { opacity: '0', transform: 'scale(0.95) translateY(10px)' },
          '100%': { opacity: '1', transform: 'scale(1) translateY(0)' },
        },
        leave: {
          '0%': { opacity: '1', transform: 'scale(1) translateY(0)' },
          '100%': { opacity: '0', transform: 'scale(0.95) translateY(10px)' },
        },
      },
    },
  },
  plugins: [],
}