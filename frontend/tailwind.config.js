/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#F97316', // Orange-500 (Fast food vibe)
          foreground: '#FFFFFF',
        },
        secondary: {
          DEFAULT: '#1F2937', // Gray-800
          foreground: '#FFFFFF',
        },
        destructive: {
          DEFAULT: '#EF4444', // Red-500
          foreground: '#FFFFFF',
        },
        muted: {
          DEFAULT: '#F3F4F6', // Gray-100
          foreground: '#6B7280', // Gray-500
        },
        accent: {
          DEFAULT: '#FDBA74', // Orange-300
          foreground: '#1F2937',
        },
      },
    },
  },
  plugins: [],
}
