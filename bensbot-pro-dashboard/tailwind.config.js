/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#2d81ff',
          50: 'rgba(45, 129, 255, 0.05)',
          100: 'rgba(45, 129, 255, 0.1)',
          200: 'rgba(45, 129, 255, 0.2)',
        },
        success: '#238636',
        warning: '#9e6a03',
        danger: '#f85149',
      },
    },
  },
  plugins: [],
}
