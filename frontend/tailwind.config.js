/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
      },
      colors: {
        ink: "#09090B",
        midnight: "#0B0F19",
        slateGlow: "#111827",
        electric: "#3B82F6",
        cyanGlow: "#22D3EE",
        violetGlow: "#8B5CF6",
      },
      boxShadow: {
        glow: "0 0 60px rgba(59, 130, 246, 0.22)",
        card: "0 24px 80px rgba(0, 0, 0, 0.35)",
      },
      backgroundImage: {
        "hero-grid":
          "linear-gradient(rgba(255,255,255,0.045) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.045) 1px, transparent 1px)",
      },
    },
  },
  plugins: [],
};
