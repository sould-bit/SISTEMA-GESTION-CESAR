/** @type {import('tailwindcss').Config} */
export default {
    darkMode: ["class"],
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            borderRadius: {
                lg: 'var(--radius)',
                md: 'calc(var(--radius) - 2px)',
                sm: 'calc(var(--radius) - 4px)'
            },
            colors: {
                "asphalt": "#0F172A",
                "asphalt-light": "#1E293B",
                "asphalt-lighter": "#334155",
                "fastops-orange": "#FF6B00",
                "alert-red": "#EF4444",
                "info-blue": "#3B82F6",
                "success-green": "#10B981",
            },
            fontFamily: {
                "sans": ["Plus Jakarta Sans", "sans-serif"],
            },
            backgroundImage: {
                'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
            }
        }
    },
    plugins: [require("tailwindcss-animate")],
}
