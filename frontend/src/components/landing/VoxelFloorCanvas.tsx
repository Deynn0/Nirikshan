import React, { useEffect, useRef } from 'react';
import { LANDING_PALETTE } from '../../landing/palette';

// ── Palette references from LANDING_PALETTE ──
const U = 0.25;
const ZN = 2;
const HAZE = LANDING_PALETTE.floor.hazeRgb;
const TOP_PURPLE = LANDING_PALETTE.floor.topLavender;
const TOP_PURPLE_BRIGHT = LANDING_PALETTE.floor.topLavenderBright;
const TOP_PURPLE_MUTED = LANDING_PALETTE.floor.topLavenderMuted;
const FRONT_PURPLE = LANDING_PALETTE.floor.frontDepth;
const SIDE_PURPLE = LANDING_PALETTE.floor.sideDepth;

function hash(a: number, b: number): number {
  let h = Math.imul(a, 374761393) + Math.imul(b, 668265263);
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967295;
}

function mix(c: [number, number, number], t: number): string {
  return `rgb(${c.map((v, i) => (v + (HAZE[i] - v) * t) | 0).join(',')})`;
}

/**
 * Draws the refined isometric voxel floor:
 * - Purple isometric grid extending toward horizon with consistent perspective and depth.
 * - Subtle, clean grid lines with lavender and light-purple top faces.
 * - Slightly darker purple side faces to create realistic depth.
 * - Naturally grouped architectural block clusters (no random noisy cubes).
 * - Smooth atmospheric transition between horizon and foreground.
 */
export function drawFloor(
  hero: HTMLElement,
  back: HTMLCanvasElement,
  front: HTMLCanvasElement,
  progress = 0,
  camX = 0,
  camY = 0,
  wristYRatio = 5.2,
): number {
  const W = hero.clientWidth;
  const H = hero.clientHeight;
  // Cap DPR at 1.75 as per technical requirements
  const dpr = Math.min(window.devicePixelRatio || 1, 1.75);

  const hor = H * 0.52;                 // Horizon Y (~52% of hero height)
  const F = (H - hor) * ZN;             // Focal depth scale
  const wristY = hor + F / wristYRatio; // Y where character hands touch floor

  const A = back.getContext('2d')!;
  const B = front.getContext('2d')!;

  const targetW = Math.round(W * dpr);
  const targetH = Math.round(H * dpr);
  if (back.width !== targetW || back.height !== targetH) {
    back.width = targetW;
    back.height = targetH;
    A.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  if (front.width !== targetW || front.height !== targetH) {
    front.width = targetW;
    front.height = targetH;
    B.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  A.clearRect(0, 0, W, H);
  B.clearRect(0, 0, W, H);

  // Project world (x, z, h) → canvas (px, py)
  const P = (x: number, z: number, h = 0): [number, number] => [
    W / 2 + ((x - camX) * F) / z,
    hor + camY * 16 + (F / z) * (1 - h),
  ];

  const poly = (
    ctx: CanvasRenderingContext2D,
    pts: [number, number][],
    col: string,
  ) => {
    ctx.fillStyle = col;
    ctx.beginPath();
    ctx.moveTo(pts[0][0], pts[0][1]);
    for (let k = 1; k < pts.length; k++) {
      ctx.lineTo(pts[k][0], pts[k][1]);
    }
    ctx.fill();
  };

  // Subtle and clean grid seams (3.2% gap fraction)
  const g = 0.032;
  const rows = 72;

  const offsetFloor = Math.floor(progress);
  const offsetFrac = progress - offsetFloor;

  // Soft atmospheric horizon bridge
  const znTop = ZN + (rows + 1 - offsetFrac) * U;
  const farY = Math.max(hor, hor + F / znTop);
  poly(A, [[0, hor], [W, hor], [W, farY + 1], [0, farY + 1]], mix(HAZE, 0.98));

  for (let r = rows + 1; r >= -1; r--) {
    const zn = ZN + (r + g - offsetFrac) * U;
    const zf = ZN + (r + 1 - g - offsetFrac) * U;

    if (zn <= 0.25) continue;

    const ctx = hor + F / zn >= wristY - 14 ? B : A;
    const t = Math.min(1, Math.max(0, (zn - 2.8) / 15)); // distance haze
    const hFade = Math.max(0, Math.min(1, (26 - zn) / 10));

    const iMax = Math.min(Math.ceil(W / 2 / ((U * F) / zn)) + 1, 38);
    const worldR = r + offsetFloor;

    for (let i = -iMax; i <= iMax; i++) {
      const a = hash(worldR, i);
      const b = hash(i + 433, worldR + 199);

      // Natural architectural clustering for raised blocks:
      // Instead of scattered noise, cluster stepped terraces naturally
      const clusterNoise = Math.sin(i * 0.45) * Math.cos(worldR * 0.35);
      const isRaisedCluster = clusterNoise > 0.42 && a > 0.70 && r < 24;
      const isSteppedTerrace = clusterNoise > 0.65 && a > 0.82 && r < 20;

      let rawH = 0;
      if (isSteppedTerrace) {
        rawH = 1.6 + b * 0.4;
      } else if (isRaisedCluster) {
        rawH = 0.9 + b * 0.3;
      }

      const xl = (i + g) * U;
      const xr = (i + 1 - g) * U;

      // Keep area right beneath hand figures smooth and grounded
      const distToHandsX = Math.abs((xl + xr) * 0.5 - 1.15);
      const distToHandsZ = Math.abs(zn - 5.2);
      if (distToHandsX < 1.1 && distToHandsZ < 0.8) {
        rawH = Math.max(0, rawH - 1.0);
      }

      // Base tile elevation provides crisp side bevel into groove
      const hBase = 0.024;
      const hBlock = rawH > 0 ? U * 0.14 * rawH * hFade : 0;
      const totalH = hBase + hBlock;

      // Clean lavender tile tone variation
      const isBright = a > 0.55;
      const isMuted = a < 0.22;
      const baseTop = isBright ? TOP_PURPLE_BRIGHT : isMuted ? TOP_PURPLE_MUTED : TOP_PURPLE;
      const v = 0.96 + b * 0.06;
      const topCol: [number, number, number] = baseTop.map(x => (x * v) | 0) as [number, number, number];
      const sideCol = mix(SIDE_PURPLE, t);
      const frontCol = mix(FRONT_PURPLE, t);

      // Render 3D side faces for depth
      if (r < 24) {
        if (xr <= camX) {
          poly(ctx, [P(xr, zn, totalH), P(xr, zf, totalH), P(xr, zf, 0), P(xr, zn, 0)], sideCol);
        } else if (xl >= camX) {
          poly(ctx, [P(xl, zn, totalH), P(xl, zf, totalH), P(xl, zf, 0), P(xl, zn, 0)], sideCol);
        }
        poly(ctx, [P(xl, zn, totalH), P(xr, zn, totalH), P(xr, zn, 0), P(xl, zn, 0)], frontCol);
      }

      // Top face in soft lavender
      poly(ctx, [P(xl, zn, totalH), P(xr, zn, totalH), P(xr, zf, totalH), P(xl, zf, totalH)], mix(topCol, t));
    }
  }

  return wristY;
}

interface VoxelFloorCanvasProps {
  onWristY?: (y: number) => void;
}

export const VoxelFloorCanvas: React.FC<VoxelFloorCanvasProps> = ({ onWristY }) => {
  const heroRef = useRef<HTMLDivElement>(null);
  const backRef = useRef<HTMLCanvasElement>(null);
  const frontRef = useRef<HTMLCanvasElement>(null);

  const progressRef = useRef(0);
  const lastTimeRef = useRef<number | null>(null);
  const lastHRef = useRef<number>(-1);
  const isVisibleRef = useRef<boolean>(true);

  // Pause rendering when scrolled out of view to save CPU/GPU
  useEffect(() => {
    if (!heroRef.current || typeof IntersectionObserver === 'undefined') return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        isVisibleRef.current = entry.isIntersecting;
      },
      { threshold: 0.05 }
    );
    observer.observe(heroRef.current);
    return () => observer.disconnect();
  }, []);

  // Stable animation loop with respect for prefers-reduced-motion
  useEffect(() => {
    let animId: number;
    const prefersReducedMotion =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const tick = (now: number) => {
      if (!isVisibleRef.current) {
        lastTimeRef.current = null;
        animId = requestAnimationFrame(tick);
        return;
      }

      if (lastTimeRef.current === null) lastTimeRef.current = now;
      const dt = Math.min((now - lastTimeRef.current) / 1000, 0.05);
      lastTimeRef.current = now;

      // Subtle, visually stable drift (paused if user prefers reduced motion)
      if (!prefersReducedMotion) {
        progressRef.current += dt * 0.45;
      }

      if (heroRef.current && backRef.current && frontRef.current) {
        const heroH = heroRef.current.clientHeight;
        const wristY = drawFloor(
          heroRef.current,
          backRef.current,
          frontRef.current,
          progressRef.current,
          0, // Stable camera X
          0, // Stable camera Y
          5.2,
        );

        if (Math.abs(heroH - lastHRef.current) > 1.0) {
          lastHRef.current = heroH;
          onWristY?.(wristY);
        }
      }

      animId = requestAnimationFrame(tick);
    };

    animId = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [onWristY]);

  return (
    <div ref={heroRef} className="absolute inset-0 pointer-events-none select-none">
      {/* BACK canvas — behind character bodies (z-0) */}
      <canvas
        ref={backRef}
        className="absolute inset-0 w-full h-full"
        style={{ zIndex: 0 }}
      />
      {/* FRONT canvas — in front of character wrist bases (z-30) */}
      <canvas
        ref={frontRef}
        className="absolute inset-0 w-full h-full"
        style={{ zIndex: 30 }}
      />
    </div>
  );
};
