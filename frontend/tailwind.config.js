/** "Analyst's ledger" design tokens -- the same palette as the mockup and the slides. */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#EAE4D3",       // page
        card: "#F3EFE3",        // raised panels
        rule: "#B9AF92",        // strong ruled lines
        "rule-soft": "#CFC6AC",
        ink: "#26241D",
        "ink-soft": "#5E5B4D",
        stamp: "#9C3B2C",       // brick-red "ink stamp": accent, warnings, losses
        gain: "#2F5D50",        // muted green: positive / done
        navy: "#1B2A4A",
      },
      fontFamily: {
        serif: ['"Source Serif 4"', "Georgia", "serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "Consolas", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
 












