import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "var(--color-paper)",
        "paper-raised": "var(--color-paper-raised)",
        ink: "var(--color-ink)",
        "ink-muted": "var(--color-ink-muted)",
        "ink-faint": "var(--color-ink-faint)",
        border: "var(--color-border)",
        accent: "var(--color-accent)",
        "accent-soft": "var(--color-accent-soft)",
        verdict: {
          green: "var(--color-verdict-green)",
          "green-bg": "var(--color-verdict-green-bg)",
          amber: "var(--color-verdict-amber)",
          "amber-bg": "var(--color-verdict-amber-bg)",
          red: "var(--color-verdict-red)",
          "red-bg": "var(--color-verdict-red-bg)",
          grey: "var(--color-verdict-grey)",
          "grey-bg": "var(--color-verdict-grey-bg)",
        },
      },
      fontFamily: {
        display: ["var(--font-fraunces)", "Georgia", "serif"],
        serif: ["var(--font-source-serif)", "Georgia", "serif"],
        sans: ["var(--font-inter)", "-apple-system", "sans-serif"],
        mono: ["var(--font-plex-mono)", "ui-monospace", "monospace"],
      },
      boxShadow: {
        paper: "0 1px 2px rgba(28, 26, 23, 0.04), 0 1px 1px rgba(28, 26, 23, 0.03)",
        raised: "0 4px 16px rgba(28, 26, 23, 0.07), 0 1px 3px rgba(28, 26, 23, 0.05)",
      },
      borderRadius: {
        sm: "4px",
        DEFAULT: "8px",
        lg: "12px",
      },
    },
  },
  plugins: [],
};

export default config;
