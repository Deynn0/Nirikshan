import React, { useEffect, useRef, useCallback } from 'react';

// ── Palette constants (verbatim from the reference drawFloor script) ──────────
const U = 0.25;
const ZN = 2;
const HAZE: [number, number, number] = [218, 210, 245];
const TOP: [number, number, number] = [200, 185, 245];
const FRONT: [number, number, number] = [155, 130, 230];
const SIDE: [number, number, number] = [175, 152, 238];

function hash(a: number, b: number): number {
  let h = Math.imul(a, 374761393) + Math.imul(b, 668265263);
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967295;
}

function mix(c: [number, number, number], t: number): string {
  return `rgb(${c.map((v, i) => (v + (HAZE[i] - v) * t) | 0).join(',')})`;
}

/**
 * Draws the isometric voxel floor onto two canvas layers.
 * Returns the wristY pixel position so the hands can be anchored there.
 */
export function drawFloor(
  hero: HTMLElement,
  back: HTMLCanvasElement,
  front: HTMLCanvasElement,
  wristYRatio = 5.2,
): number {
  const W = hero.clientWidth;
  const H = hero.clientHeight;
  const dpr = window.devicePixelRatio || 1;

  const hor = H * 0.4;           // horizon Y
  const F = (H - hor) * ZN;    // focal depth scale
  const wristY = hor + F / wristYRatio; // Y where hands touch the floor

  const A = back.getContext('2d')!;
  const B = front.getContext('2d')!;

  [back, front].forEach(c => {
    c.width = W * dpr;
    c.height = H * dpr;
  });
  [A, B].forEach(c => c.setTransform(dpr, 0, 0, dpr, 0, 0));

  // Project world (x, z, h) → canvas (px, py)
  const P = (x: number, z: number, h = 0): [number, number] => [
    W / 2 + (x * F) / z,
    hor + (F / z) * (1 - h),
  ];

  const poly = (
    ctx: CanvasRenderingContext2D,
    pts: [number, number][],
    col: string,
  ) => {
    ctx.fillStyle = col;
    ctx.beginPath();
    pts.forEach((p, i) => (i ? ctx.lineTo(...p) : ctx.moveTo(...p)));
    ctx.fill();
  };

  const g = 0;
  const rows = Math.floor(((U * F) / 4 - ZN) / U);

  for (let r = rows; r >= 0; r--) {
    const zn = ZN + (r + g) * U;
    const zf = ZN + (r + 1 - g) * U;

    // Near rows go into the FRONT canvas (drawn over the hand wrists)
    const ctx = hor + F / zn >= wristY - 18 ? B : A;

    const t = Math.min(1, Math.max(0, (zn - 3) / 38)); // distance haze
    const iMax = Math.ceil(W / 2 / ((U * F) / zn)) + 2;

    for (let i = -iMax; i <= iMax; i++) {
      const a = hash(r, i);
      const b = hash(i + 999, r + 77);

      const h = U * 0.08 * ([0, 0, 1, 0, 2, 1, 0, 2, 3][Math.floor(a * 9)] ?? 0);
      const xl = (i + g) * U;
      const xr = (i + 1 - g) * U;
      const v = 0.9 + b * 0.1;
      const topCol: [number, number, number] = TOP.map(x => (x * v) | 0) as [number, number, number];

      if (h > 0) {
        // Side face
        if (xr < 0) poly(ctx, [P(xr, zn, h), P(xr, zf, h), P(xr, zf), P(xr, zn)], mix(SIDE, t));
        else if (xl > 0) poly(ctx, [P(xl, zn, h), P(xl, zf, h), P(xl, zf), P(xl, zn)], mix(SIDE, t));
        // Front face
        poly(ctx, [P(xl, zn, h), P(xr, zn, h), P(xr, zn), P(xl, zn)], mix(FRONT, t));
      } else {
        // Flat tile front ledge
        poly(ctx, [P(xl, zn, 0.012), P(xr, zn, 0.012), P(xr, zn), P(xl, zn)], mix(FRONT, t));
      }
      // Top face (always)
      poly(ctx, [P(xl, zn, h), P(xr, zn, h), P(xr, zf, h), P(xl, zf, h)], mix(topCol, t));
    }
  }

  return wristY;
}

// ── React component ───────────────────────────────────────────────────────────

interface VoxelFloorCanvasProps {
  /** Callback fired after every draw with the computed wristY pixel value */
  onWristY?: (y: number) => void;
}

export const VoxelFloorCanvas: React.FC<VoxelFloorCanvasProps> = ({ onWristY }) => {
  const heroRef = useRef<HTMLDivElement>(null);
  const backRef = useRef<HTMLCanvasElement>(null);
  const frontRef = useRef<HTMLCanvasElement>(null);

  const redraw = useCallback(() => {
    if (!heroRef.current || !backRef.current || !frontRef.current) return;
    const y = drawFloor(heroRef.current, backRef.current, frontRef.current);
    onWristY?.(y);
  }, [onWristY]);

  useEffect(() => {
    redraw();
    window.addEventListener('resize', redraw);
    return () => window.removeEventListener('resize', redraw);
  }, [redraw]);

  return (
    // heroRef spans the full hero section so W/H match exactly
    <div ref={heroRef} className="absolute inset-0 pointer-events-none select-none">
      {/* BACK canvas — behind the hands (z-0) */}
      <canvas
        ref={backRef}
        className="absolute inset-0 w-full h-full"
        style={{ zIndex: 0 }}
      />
      {/* FRONT canvas — in front of the hand wrists (z-30) */}
      <canvas
        ref={frontRef}
        className="absolute inset-0 w-full h-full"
        style={{ zIndex: 30 }}
      />
    </div>
  );
};
