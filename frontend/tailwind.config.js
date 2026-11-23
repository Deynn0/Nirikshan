/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        canvas: 'var(--lp-canvas, #fbf8f5)',
        surface: 'var(--lp-surface, #ffffff)',
        'surface-2': 'var(--lp-surface-2, #f6f1ee)',
        'surface-3': 'var(--lp-surface-3, #efe8e6)',
        ink: 'var(--lp-ink, #1c1622)',
        'ink-2': 'var(--lp-ink-2, #4a4252)',
        'ink-3': 'var(--lp-ink-3, #6f6679)',
        'ink-4': 'var(--lp-ink-4, #aaa1b0)',
        line: 'var(--lp-line, #ece4e5)',
        'line-2': 'var(--lp-line-2, #dfd4d8)',
        'mismatch-bg': 'var(--lp-mismatch-bg, #fdebec)',
        'mismatch-fg': 'var(--lp-mismatch-fg, #b4232a)',
        'brand-solid': '#7428ea',
        background: {
          light: '#FAF8F4',
          dark: '#0B0F19',
        },
        card: {
          border: '#E8E5DF',
        },
        primary: {
          50: '#F5F3FF',
          100: '#EDE9FE',
          200: '#DDD6FE',
          300: '#C4B5FD',
          400: '#A78BFA',
          500: '#8B5CF6',
          600: '#7C3AED',
          700: '#6D28D9',
          800: '#5B21B6',
          900: '#4C1D95',
        },
        severity: {
          critical: '#EF4444',
          contradicted: '#DC2626',
          warning: '#F59E0B',
          verified: '#10B981',
          proven: '#059669',
          neutral: '#6B7280',
        },
        brand: {
          50: '#f5f0ff',
          100: '#ebe0ff',
          200: '#d6c2ff',
          300: '#ba99ff',
          400: '#9e6dff',
          500: '#8b3dff',
          600: '#7428ea',
          700: '#5d1fc2',
          800: '#47198f',
          900: '#2b0f5c',
          950: '#1b083c',
        },
        trust: {
          crypto: '#8b5cf6',
          statutory: '#3b82f6',
          hardened: '#06b6d4',
          model: '#f59e0b',
          unverified: '#ef4444',
        }
      },
      fontFamily: {
        sans: ['Inter', 'Plus Jakarta Sans', 'system-ui', 'sans-serif'],
        display: ['"Inter Tight"', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        xs: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        soft: '0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.04)',
        card: '0 4px 6px -1px rgba(0, 0, 0, 0.03), 0 2px 4px -2px rgba(0, 0, 0, 0.03)',
        floating: '0 20px 25px -5px rgba(0, 0, 0, 0.07), 0 8px 10px -6px rgba(0, 0, 0, 0.04)',
      },
      borderRadius: {
        control: '10px',
        card: '16px',
      }
    },
  },
  plugins: [],
}
