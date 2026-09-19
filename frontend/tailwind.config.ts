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
        // Foreground ink (on-surface / parchment variant / muted label)
        ink: {
          DEFAULT: '#E2E2EB',
          variant: '#D0C5AF',
          muted: '#948C79',
        },
        // Hairline gilded wireframe used to frame glass surfaces
        rim: {
          DEFAULT: 'rgba(212, 175, 55, 0.14)',
          soft: 'rgba(212, 175, 55, 0.10)',
          strong: 'rgba(212, 175, 55, 0.40)',
        },
      },
      fontFamily: {
        display: ['"Noto Serif SC"', '"Noto Serif"', '"Songti SC"', 'serif'],
        body: ['Inter', '"Noto Sans SC"', 'system-ui', 'sans-serif'],
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
