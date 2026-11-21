/**
 * Nirikshan Landing Page Design Tokens & Palette
 * Reference: Atmospheric sky, purple voxel landscape, and character palette
 */

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
    // Horizon lilac-cream haze
    hazeRgb: [236, 227, 250] as [number, number, number],
    // Clean pastel lavender top faces
    topLavender: [206, 186, 250] as [number, number, number],       // #CEBAFA
    topLavenderBright: [222, 206, 255] as [number, number, number], // #DECEFF
    topLavenderMuted: [194, 172, 244] as [number, number, number],  // #C2ACF4
    // Side & Front depth faces (slightly darker purple for depth)
    frontDepth: [130, 96, 218] as [number, number, number],         // #8260DA
    sideDepth: [150, 118, 228] as [number, number, number],         // #9676E4
    // Groove seam line
    grooveSeam: [112, 78, 202] as [number, number, number],        // #704ECA
  },

  // ── Two Hand Characters Palette ──
  characters: {
    pink: {
      skin: '#EB8298',
      ring: '#DB657E',
      ringOuterDot: '#FFFFFF',
      ringFingerDot: '#FEE08B', // Warm yellow dot accent
      pupil: '#111111',
      glint: '#FFFFFF',
      sclera: '#FFFFFF',
      dropShadow: 'drop-shadow(0 16px 30px rgba(235, 130, 152, 0.25))',
    },
    purple: {
      skin: '#7839EE',
      ring: '#6023D8',
      ringOuterDot: '#FFFFFF',
      ringFingerDot: '#FEE08B', // Warm yellow dot accent
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

