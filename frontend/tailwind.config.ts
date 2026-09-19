import type { Config } from 'tailwindcss';

// Celestial Obsidian design tokens ported from design/celestial_obsidian/DESIGN.md.
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Void & canvas (obsidian deep)
        void: '#0B0D13',
        surface: {
          DEFAULT: '#121622',
          raised: '#171C2B',
        },
        // Celestial gold
        gold: {
          DEFAULT: '#D4AF37',
          bright: '#F5D77F',
          soft: '#E6C65C',
          muted: '#997B24',
        },
        // Eastern five elements (wuxing)
        wuxing: {
          wood: '#2DD4BF',
          fire: '#F43F5E',
          earth: '#EAB308',
          metal: '#F1F5F9',
          water: '#38BDF8',
        },
        // Western celestial & esoteric accents
        astral: '#818CF8',
        arcane: '#A855F7',
      },
      fontFamily: {
        display: ['"Noto Serif"', 'serif'],
        body: ['Inter', 'sans-serif'],
        numeric: ['"Space Grotesk"', 'monospace'],
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
