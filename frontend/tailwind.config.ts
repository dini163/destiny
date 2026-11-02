import type { Config } from 'tailwindcss';

// Celestial Obsidian design tokens ported from design/celestial_obsidian/DESIGN.md.
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Void & canvas (obsidian deep)
        void: 'rgb(var(--void-rgb) / <alpha-value>)',
        surface: {
          DEFAULT: 'rgb(var(--surface-1-rgb) / <alpha-value>)',
          raised: 'rgb(var(--surface-2-rgb) / <alpha-value>)',
        },
        // Celestial gold
        gold: {
          DEFAULT: 'rgb(var(--gold-rgb) / <alpha-value>)',
          bright: 'rgb(var(--gold-bright-rgb) / <alpha-value>)',
          soft: 'rgb(var(--gold-soft-rgb) / <alpha-value>)',
          muted: 'rgb(var(--gold-muted-rgb) / <alpha-value>)',
        },
        // Eastern five elements (wuxing)
        wuxing: {
          wood: 'rgb(var(--wuxing-wood-rgb) / <alpha-value>)',
          fire: 'rgb(var(--wuxing-fire-rgb) / <alpha-value>)',
          earth: 'rgb(var(--wuxing-earth-rgb) / <alpha-value>)',
          metal: 'rgb(var(--wuxing-metal-rgb) / <alpha-value>)',
          water: 'rgb(var(--wuxing-water-rgb) / <alpha-value>)',
        },
        // Western celestial & esoteric accents
        astral: 'rgb(var(--astral-rgb) / <alpha-value>)',
        arcane: 'rgb(var(--arcane-rgb) / <alpha-value>)',
        // Foreground ink (on-surface / parchment variant / muted label)
        ink: {
          DEFAULT: 'rgb(var(--ink-rgb) / <alpha-value>)',
          variant: 'rgb(var(--ink-variant-rgb) / <alpha-value>)',
          muted: 'rgb(var(--ink-muted-rgb) / <alpha-value>)',
        },
        // Hairline gilded wireframe used to frame glass surfaces
        rim: {
          DEFAULT: 'rgb(var(--rim-rgb) / 0.25)',
          soft: 'rgb(var(--rim-rgb) / 0.15)',
          strong: 'rgb(var(--rim-rgb) / 0.55)',
        },
      },
      fontFamily: {
        display: ['"Noto Serif SC"', '"Noto Serif"', '"Songti SC"', 'serif'],
        body: ['"Microsoft YaHei"', '"PingFang SC"', 'system-ui', 'sans-serif'],
        numeric: ['"Space Grotesk"', '"Noto Sans SC"', 'monospace'],
      },
      spacing: {
        gutter: '1.5rem',
        margin: '2.5rem',
      },
      borderRadius: {
        element: '4px',
        card: '8px',
      },
      boxShadow: {
        'gold-rim': 'inset 0 1px 0 0 rgba(245, 215, 127, 0.2)',
        'astral-halo': '0 0 40px -10px rgba(212, 175, 55, 0.25), 0 20px 40px -15px rgba(0, 0, 0, 0.9)',
      },
    },
  },
  plugins: [],
} satisfies Config;
