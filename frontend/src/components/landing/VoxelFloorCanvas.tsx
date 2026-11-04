import React, { useEffect, useRef } from 'react';

// ── Exact Palette Sampled from Reference Image (Zero Green, Zero Mud) ─────────
const U = 0.25;
const ZN = 2;
const HAZE: [number, number, number] = [238, 230, 252]; // horizon lilac-cream haze

// Pastel lavender-purple tiles
const TOP_PURPLE: [number, number, number] = [206, 188, 252];       // #CEBCFC - clean pastel lilac
const TOP_PURPLE_BRIGHT: [number, number, number] = [214, 196, 254]; // #D6C4FE - highlight tile
const FRONT_PURPLE: [number, number, number] = [136, 104, 216];     // #8868D8 - front shadow
const SIDE_PURPLE: [number, number, number] = [156, 126, 228];      // #9C7EE4 - side shadow
const GROOVE_PURPLE: [number, number, number] = [120, 92, 202];     // #785CCA - tile groove/seam line

function hash(a: number, b: number): number {
  let h = Math.imul(a, 374761393) + Math.imul(b, 668265263);
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967295;
}

function mix(c: [number, number, number], t: number): string {
  return `rgb(${c.map((v, i) => (v + (HAZE[i] - v) * t) | 0).join(',')})`;
}

// ── Flying box particle for the pop-out explosion ───────────────────────────
interface FlyingBox {
  x0: number;
  z0: number;
  vx: number;
  vy: number;
  vz: number;
  sx: number;
  sz: number;
  sh: number;
  delay: number;
  isBright: boolean;
}

function initFlyingBoxes(): FlyingBox[] {
  const boxes: FlyingBox[] = [];
  for (let i = 0; i < 34; i++) {
    const angle = (i / 34) * Math.PI * 2 + (hash(i, 77) - 0.5) * 0.4;
    const speed = 2.2 + hash(i, 19) * 3.8;
    boxes.push({
      x0: 1.2 + (hash(i, 31) - 0.5) * 1.5,
      z0: 5.2 + (hash(i, 53) - 0.5) * 0.9,
      vx: Math.cos(angle) * speed,
      vz: Math.sin(angle) * (speed * 0.8),
      vy: 4.8 + hash(i, 89) * 4.4, // explosive upward lift
      sx: 0.16 + hash(i, 41) * 0.16,
      sz: 0.16 + hash(i, 67) * 0.16,
      sh: 0.12 + hash(i, 101) * 0.18,
      delay: 0.12 + hash(i, 23) * 0.32,
      isBright: hash(i, 11) > 0.5,
    });
  }
  return boxes;
}

/**
 * Draws the isometric voxel floor with distinct tile seams and raised 3D rectangular blocks.
 */
export function drawFloor(
  hero: HTMLElement,
  back: HTMLCanvasElement,
  front: HTMLCanvasElement,
  progress = 0,
  camX = 0,
  camY = 0,
  wristYRatio = 5.2,
  elapsed = 999,
  flyingBoxes?: FlyingBox[],
): number {
  const W = hero.clientWidth;
  const H = hero.clientHeight;
  const dpr = Math.min(window.devicePixelRatio || 1, 1.5);

  const hor = H * 0.43;                 // horizon Y (~43% of hero height)
  const F = (H - hor) * ZN;           // focal depth scale
  const wristY = hor + F / wristYRatio; // Y where hands touch the floor

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
    hor + camY * 18 + (F / z) * (1 - h),
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

  // Gap fraction: 4.5% gap creates visible tile grooves
  const g = 0.045;
  // Uniform rows with identical box length U = 0.25 across the entire floor
  const rows = 75;

  const offsetFloor = Math.floor(progress);
  const offsetFrac = progress - offsetFloor;

  // Seamless horizon haze bridge from hor to the first row (ensuring 0px gap to sky)
  const znTop = ZN + (rows + 1 - offsetFrac) * U;
  const farY = Math.max(hor, hor + F / znTop);
  poly(A, [[0, hor], [W, hor], [W, farY + 1.5], [0, farY + 1.5]], mix(HAZE, 0.98));

  for (let r = rows + 1; r >= -1; r--) {
    // Every single row has the exact same uniform box length: zf - zn = (1 - 2*g) * U
    const zn = ZN + (r + g - offsetFrac) * U;
    const zf = ZN + (r + 1 - g - offsetFrac) * U;

    if (zn <= 0.25) continue;

    const ctx = hor + F / zn >= wristY - 18 ? B : A;
    const t = Math.min(1, Math.max(0, (zn - 3) / 16)); // distance haze
    const hFade = Math.max(0, Math.min(1, (28 - zn) / 12));

    const iMax = Math.min(Math.ceil(W / 2 / ((U * F) / zn)) + 1, 36);
    const worldR = r + offsetFloor;

    for (let i = -iMax; i <= iMax; i++) {
      const a = hash(worldR, i);
      const b = hash(i + 999, worldR + 77);

      const isBright = hash(worldR * 13, i * 29) > 0.45;

      // Clean structured pattern matching the reference image:
      // Most tiles are uniform ground tiles; ~18% are raised into crisp 3D rectangular blocks
      const isRaised = a > 0.82 && r < 30;
      const isDouble = a > 0.94 && r < 30;

      let rawH = 0;
      if (isRaised) {
        rawH = isDouble ? 2.4 + b * 0.6 : 1.3 + b * 0.4;
      }

      const xl = (i + g) * U;
      const xr = (i + 1 - g) * U;

      // Sunken entrance crater right where hands emerge (around zn ~ 5.2, world X ~ 0.5 to 1.8)
      const distToCraterX = Math.abs((xl + xr) * 0.5 - 1.2);
      const distToCraterZ = Math.abs(zn - 5.2);
      if (distToCraterX < 1.4 && distToCraterZ < 0.8) {
        rawH = Math.max(-0.4, rawH - 1.3);
      }

      // Base tile elevation ensures front and side shadow bevels drop into the groove
      const hBase = 0.026;
      const hBlock = rawH > 0 ? U * 0.16 * rawH * hFade : 0;
      const totalH = hBase + hBlock;

      const v = 0.94 + b * 0.08;
      const baseTop = isBright ? TOP_PURPLE_BRIGHT : TOP_PURPLE;
      const topCol: [number, number, number] = baseTop.map(x => (x * v) | 0) as [number, number, number];
      const sideCol = mix(SIDE_PURPLE, t);
      const frontCol = mix(FRONT_PURPLE, t);

      // Distant rows near horizon only need top face (ultra-fast, zero gap)
      if (r < 26) {
        if (xr <= camX) {
          poly(ctx, [P(xr, zn, totalH), P(xr, zf, totalH), P(xr, zf, 0), P(xr, zn, 0)], sideCol);
        } else if (xl >= camX) {
          poly(ctx, [P(xl, zn, totalH), P(xl, zf, totalH), P(xl, zf, 0), P(xl, zn, 0)], sideCol);
        }
        poly(ctx, [P(xl, zn, totalH), P(xr, zn, totalH), P(xr, zn, 0), P(xl, zn, 0)], frontCol);
      }

      // Top face (luminous pastel lilac extending seamlessly right to hor)
      poly(ctx, [P(xl, zn, totalH), P(xr, zn, totalH), P(xr, zf, totalH), P(xl, zf, totalH)], mix(topCol, t));
    }
  }

  // ── Render flying boxes explosion during load entrance (elapsed < 2.2s) ──
  if (flyingBoxes && elapsed < 2.2) {
    for (let k = 0; k < flyingBoxes.length; k++) {
      const box = flyingBoxes[k];
      const dtBox = elapsed - box.delay;
      if (dtBox > 0 && dtBox < 1.8) {
        const bx = box.x0 + box.vx * dtBox;
        const bz = box.z0 + box.vz * dtBox;
        const bh = Math.max(0, box.vy * dtBox - 0.5 * 11.5 * dtBox * dtBox);

        if (bh > 0.005 && bz > 1.2) {
          const sx = box.sx;
          const sz = box.sz;
          const sh = box.sh;

          const bTop = box.isBright ? TOP_PURPLE_BRIGHT : TOP_PURPLE;
          const topCol = mix(bTop, 0.04);
          const frontCol = mix(FRONT_PURPLE, 0.04);
          const sideCol = mix(SIDE_PURPLE, 0.04);

          poly(B, [P(bx, bz, bh + sh), P(bx + sx, bz, bh + sh), P(bx + sx, bz + sz, bh + sh), P(bx, bz + sz, bh + sh)], topCol);
          poly(B, [P(bx, bz, bh + sh), P(bx + sx, bz, bh + sh), P(bx + sx, bz, bh), P(bx, bz, bh)], frontCol);
          poly(B, [P(bx + sx, bz, bh + sh), P(bx + sx, bz + sz, bh + sh), P(bx + sx, bz + sz, bh), P(bx + sx, bz, bh)], sideCol);
        }
      }
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

  const progressRef = useRef(0);
  const lastTimeRef = useRef<number | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const lastHRef = useRef<number>(-1);
  const isVisibleRef = useRef<boolean>(true);
  const flyingBoxesRef = useRef<FlyingBox[]>(initFlyingBoxes());

  // Pause rendering when scrolled out of view to save 100% CPU
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

  // Smooth animation loop: land does NOT move with cursor (camX=0, camY=0)
  useEffect(() => {
    let animId: number;

    const tick = (now: number) => {
      if (!isVisibleRef.current) {
        lastTimeRef.current = null;
        animId = requestAnimationFrame(tick);
        return;
      }

      if (startTimeRef.current === null) startTimeRef.current = now;
      const elapsed = (now - startTimeRef.current) / 1000;

      if (lastTimeRef.current === null) lastTimeRef.current = now;
      const dt = Math.min((now - lastTimeRef.current) / 1000, 0.05);
      lastTimeRef.current = now;

      // Steady gentle forward progression
      progressRef.current += dt * 0.72;

      if (heroRef.current && backRef.current && frontRef.current) {
        const heroH = heroRef.current.clientHeight;
        const wristY = drawFloor(
          heroRef.current,
          backRef.current,
          frontRef.current,
          progressRef.current,
          0, // camX locked: land does NOT move with cursor
          0, // camY locked: land does NOT move with cursor
          5.2,
          elapsed,
          flyingBoxesRef.current,
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
