/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", '"Segoe UI"', "sans-serif"],
      },
      colors: {
        ink: "#05070A",
        midnight: "#0B0F19",
        slateGlow: "#111827",
        electric: "#3B82F6",
        cyanGlow: "#22D3EE",
        violetGlow: "#8B5CF6",
        indigoGlow: "#6366F1",
      },
      boxShadow: {
        glow: "0 0 60px rgba(59, 130, 246, 0.22)",
        "glow-cyan": "0 0 60px rgba(34, 211, 238, 0.28)",
        "glow-violet": "0 0 60px rgba(139, 92, 246, 0.28)",
        "glow-strong": "0 18px 60px rgba(34, 211, 238, 0.35)",
        card: "0 24px 80px rgba(0, 0, 0, 0.45)",
        "card-soft": "0 12px 40px rgba(0, 0, 0, 0.35)",
        "inner-soft": "inset 0 1px 0 0 rgba(255, 255, 255, 0.06)",
      },
      backgroundImage: {
        "hero-grid":
          "linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)",
        "premium-radial":
          "radial-gradient(circle at top, rgba(59,130,246,0.18), transparent 34rem), radial-gradient(circle at 20% 30%, rgba(139,92,246,0.16), transparent 30rem), linear-gradient(180deg, #05070A 0%, #0B0F19 48%, #05070A 100%)",
        "card-sheen":
          "linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.015) 100%)",
      },
      letterSpacing: {
        tightest: "-0.06em",
      },
      animation: {
        "pulse-soft": "pulseSoft 2.4s ease-in-out infinite",
        shimmer: "shimmer 2.6s linear infinite",
      },
      keyframes: {
        pulseSoft: {
          "0%, 100%": { opacity: "0.55" },
          "50%": { opacity: "1" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
    },
  },
  plugins: [],
};
