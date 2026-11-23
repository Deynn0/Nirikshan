import type { CSSProperties } from "react";

// Landing palette; values mirror the tokens in frontend/DESIGN.md
export const palette = {
  canvas: "#fbf8f5",
  surface: "#ffffff",
  surface2: "#f6f1ee",
  surface3: "#efe8e6",
  ink: "#1c1622",
  ink2: "#4a4252",
  ink3: "#6f6679",
  ink4: "#aaa1b0",
  line: "#ece4e5",
  line2: "#dfd4d8",
  brand: {
    50: "#f5f0ff",
    100: "#ebe0ff",
    200: "#d6c2ff",
    300: "#ba99ff",
    400: "#9e6dff",
    500: "#8b3dff",
    600: "#7428ea",
    700: "#5d1fc2",
    800: "#47198f",
    900: "#2b0f5c",
  },
  peach: "#ffe1c9",
  apricot: "#ffcfa8",
  rose: "#f8cde0",
  lilac: "#e2d3ff",
  pupil: "#120c1c",
  pupil2: "#1d1430",
  status: {
    verified: { fg: "#12723a", bg: "#e7f6ec", dot: "#1fa055" },
    mismatch: { fg: "#b4232a", bg: "#fdebec", dot: "#e5484d" },
    expired: { fg: "#a2440e", bg: "#fff0e4", dot: "#f76b15" },
    pending: { fg: "#2b4fc2", bg: "#ebf0fe", dot: "#3e63dd" },
    unavail: { fg: "#4c4a55", bg: "#f0eff2", dot: "#79768a" },
    manual: { fg: "#8a5a00", bg: "#fdf4d6", dot: "#d9a106" },
    unchecked: { fg: "#6b6874", bg: "#f3f2f4", dot: "#b3b0ba" },
  },
  ev: ["#0f5f3a", "#1f8a50", "#2f5ad6", "#7428ea", "#c2550f", "#d39b0a", "#9a94a3"],
  // WebGL voxel materials
  voxel: {
    top: "#c8b6f5",
    side: "#8f6fd8",
    sideDeep: "#5f43b3",
    rim: "#ffd9bf",
    irisInner: "#7a36ee",
    irisMid: "#b45ee0",
    irisOuter: "#f3a3c7",
    limbal: "#3b157f",
    lens: "#fffaf6",
  },
} as const;

export type StatusKey = keyof typeof palette.status;

// CSS custom properties for the landing root; use as text-(--lp-ink), bg-(--lp-canvas) and so on
export const landingVars = {
  "--lp-canvas": palette.canvas,
  "--lp-surface": palette.surface,
  "--lp-surface-2": palette.surface2,
  "--lp-surface-3": palette.surface3,
  "--lp-ink": palette.ink,
  "--lp-ink-2": palette.ink2,
  "--lp-ink-3": palette.ink3,
  "--lp-ink-4": palette.ink4,
  "--lp-line": palette.line,
  "--lp-line-2": palette.line2,
  "--lp-brand-50": palette.brand[50],
  "--lp-brand-100": palette.brand[100],
  "--lp-brand-200": palette.brand[200],
  "--lp-brand-300": palette.brand[300],
  "--lp-brand-400": palette.brand[400],
  "--lp-brand-500": palette.brand[500],
  "--lp-brand-600": palette.brand[600],
  "--lp-brand-700": palette.brand[700],
  "--lp-brand-800": palette.brand[800],
  "--lp-brand-900": palette.brand[900],
  "--lp-peach": palette.peach,
  "--lp-apricot": palette.apricot,
  "--lp-rose": palette.rose,
  "--lp-lilac": palette.lilac,
  "--lp-pupil": palette.pupil,
  "--lp-pupil-2": palette.pupil2,
  "--lp-verified-fg": palette.status.verified.fg,
  "--lp-verified-bg": palette.status.verified.bg,
  "--lp-verified-dot": palette.status.verified.dot,
  "--lp-mismatch-fg": palette.status.mismatch.fg,
  "--lp-mismatch-bg": palette.status.mismatch.bg,
  "--lp-mismatch-dot": palette.status.mismatch.dot,
  "--lp-manual-fg": palette.status.manual.fg,
  "--lp-manual-bg": palette.status.manual.bg,
  "--lp-manual-dot": palette.status.manual.dot,
  "--lp-pending-fg": palette.status.pending.fg,
  "--lp-pending-bg": palette.status.pending.bg,
  "--lp-pending-dot": palette.status.pending.dot,
  "--lp-voxel-top": palette.voxel.top,
  "--lp-voxel-side": palette.voxel.side,
} as CSSProperties;

export const LANDING_PALETTE = {
  // ── Atmospheric Background Gradient Tokens ──
  sky: {
    peachTop: '#FDB695',       // Peach at the top
    apricotUpper: '#FDC7AB',    // Soft apricot in upper-middle
    rosePinkMiddle: '#F7D6E0',  // Pink/rose in middle
    lilacHorizon: '#ECE3FA',    // Light lilac near horizon & floor
    gradient: 'linear-gradient(180deg, #FDB695 0%, #FDC7AB 18%, #FDDBCB 32%, #FEEBDF 44%, #F7E4EE 54%, #EFE4FB 68%, #E4D5F8 82%, #CEBCFC 100%)',
    atmosphericBacklight: 'radial-gradient(circle at 72% 48%, rgba(255, 255, 255, 0.40) 0%, rgba(255, 240, 246, 0.22) 42%, transparent 72%)',
    headlineGlow: 'radial-gradient(ellipse 60% 50% at 25% 45%, rgba(255, 255, 255, 0.85) 0%, rgba(255, 255, 255, 0.45) 45%, transparent 80%)',
  },

  // ── 3D Voxel Floor Tokens ──
  floor: {
    hazeRgb: [236, 227, 250] as [number, number, number],
    topLavender: [206, 186, 250] as [number, number, number],
    topLavenderBright: [222, 206, 255] as [number, number, number],
    topLavenderMuted: [194, 172, 244] as [number, number, number],
    frontDepth: [130, 96, 218] as [number, number, number],
    sideDepth: [150, 118, 228] as [number, number, number],
    grooveSeam: [112, 78, 202] as [number, number, number],
  },

  // ── Two Hand Characters Palette ──
  characters: {
    pink: {
      skin: '#EB8298',
      ring: '#DB657E',
      ringOuterDot: '#FFFFFF',
      ringFingerDot: '#FEE08B',
      pupil: '#111111',
      glint: '#FFFFFF',
      sclera: '#FFFFFF',
      dropShadow: 'drop-shadow(0 16px 30px rgba(235, 130, 152, 0.25))',
    },
    purple: {
      skin: '#7839EE',
      ring: '#6023D8',
      ringOuterDot: '#FFFFFF',
      ringFingerDot: '#FEE08B',
      pupil: '#111111',
      glint: '#FFFFFF',
      sclera: '#FFFFFF',
      dropShadow: 'drop-shadow(0 16px 30px rgba(120, 57, 238, 0.25))',
    },
    commonShadow: 'drop-shadow(0 20px 36px rgba(45, 10, 80, 0.14))',
  },

  // ── Typography & UI Tokens ──
  ui: {
    inkHeadline: '#0F172A',
    inkDescription: '#475569',
    brandViolet: '#7B24E7',
    brandVioletHover: '#6A1BD6',
    brandVioletActive: '#5815B6',
    brandVioletShadow: '0 4px 18px rgba(123, 36, 231, 0.35)',
    brandVioletShadowHover: '0 6px 24px rgba(123, 36, 231, 0.45)',
    secondaryBtnBg: 'rgba(255, 255, 255, 0.55)',
    secondaryBtnBgHover: 'rgba(255, 255, 255, 0.85)',
    secondaryBtnBorder: 'rgba(214, 211, 209, 0.85)',
    secondaryBtnText: '#1E293B',
    badgeBg: 'rgba(255, 255, 255, 0.85)',
    badgeBorder: 'rgba(255, 255, 255, 0.90)',
    badgeText: '#7C3AED',
    navbarBg: 'rgba(255, 255, 255, 0.92)',
    navbarBorder: 'rgba(255, 255, 255, 0.95)',
    navbarShadow: '0 4px 24px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0, 0, 0, 0.02)',
  },
} as const;
