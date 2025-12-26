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
          50: '#edf2ff',
          100: '#dbe7ff',
          200: '#bed2ff',
          300: '#9ab9ff',
          400: '#6e96ff',
          500: '#3f72f2',
          600: '#2b5ed6',
          700: '#1e4ab3',
          800: '#16388a',
          900: '#0f1f3b',
        },
        accent: {
          50: '#fff7ed',
          100: '#fdebd9',
          200: '#f8d1b1',
          300: '#f6b989',
          400: '#f4a261',
          500: '#e8894b',
        },
        ink: '#0f172a',
        mist: '#f8fafc',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}
