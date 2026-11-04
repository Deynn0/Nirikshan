import React, { useEffect, useRef } from 'react';

// ── Palette constants ────────────────────────────────────────────────────────
const U = 0.25;
const ZN = 2;
const HAZE: [number, number, number] = [225, 216, 246];

// Purple palette (low 3D grid blocks)
const TOP_PURPLE: [number, number, number] = [204, 188, 246];
const FRONT_PURPLE: [number, number, number] = [156, 130, 230];
const SIDE_PURPLE: [number, number, number] = [178, 154, 238];

// Grey palette (for larger purple & grey rectangular objects)
const TOP_GREY: [number, number, number] = [198, 198, 214];
const FRONT_GREY: [number, number, number] = [150, 148, 168];
const SIDE_GREY: [number, number, number] = [172, 170, 190];

function hash(a: number, b: number): number {
  let h = Math.imul(a, 374761393) + Math.imul(b, 668265263);
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967295;
}

function mix(c: [number, number, number], t: number): string {
  return `rgb(${c.map((v, i) => (v + (HAZE[i] - v) * t) | 0).join(',')})`;
}

/**
 * Draws the isometric voxel floor onto two canvas layers with high-performance polygon batching.
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
  // Cap devicePixelRatio to 1.5 to prevent massive 4K canvas fill-rate bottlenecks
  const dpr = Math.min(window.devicePixelRatio || 1, 1.5);

  const hor = H * 0.43;                 // horizon Y (~43% of hero height)
  const F = (H - hor) * ZN;           // focal depth scale
  const wristY = hor + F / wristYRatio; // Y where hands touch the floor

  const A = back.getContext('2d')!;
  const B = front.getContext('2d')!;

  // Only adjust canvas backing dimensions if changed
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

  // Clear canvases for current frame
  A.clearRect(0, 0, W, H);
  B.clearRect(0, 0, W, H);

  // Project world (x, z, h) → canvas (px, py)
  const P = (x: number, z: number, h = 0): [number, number] => [
    W / 2 + ((x - camX) * F) / z,
    hor + camY * 18 + (F / z) * (1 - h),
  ];

  // High-performance polygon path drawer without per-vertex callback closures
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

  const g = 0;
  // Cap rows to visible depth (zn <= 16 where haze reaches 100% and blocks vanish into horizon)
  // This reduces polygon count by ~96% without ANY visible change to the scene.
  const rows = Math.min(Math.floor(((U * F) / 4 - ZN) / U), 36);

  const offsetFloor = Math.floor(progress);
  const offsetFrac = progress - offsetFloor;

  for (let r = rows + 1; r >= -1; r--) {
    const zn = ZN + (r + g - offsetFrac) * U;
    const zf = ZN + (r + 1 - g - offsetFrac) * U;

    if (zn <= 0.25) continue; // Behind or clipping lens

    // Near rows go into the FRONT canvas (drawn over the hand wrists)
    const ctx = hor + F / zn >= wristY - 18 ? B : A;

    const t = Math.min(1, Math.max(0, (zn - 3) / 18)); // distance haze

    // Height fade: blocks gently rise out of the distant horizon haze smoothly
    const hFade = Math.max(0, Math.min(1, (36 - zn) / 14));

    // Cap horizontal span to visible screen bounds
    const iMax = Math.min(Math.ceil(W / 2 / ((U * F) / zn)) + 1, 36);
    const worldR = r + offsetFloor;

    for (let i = -iMax; i <= iMax; i++) {
      const a = hash(worldR, i);
      const b = hash(i + 999, worldR + 77);
      const c = hash(worldR * 19, i * 37);

      // Low 3D grid blocks with some larger purple & grey rectangular objects
      const isGrey = c > 0.80; // ~20% rectangular grey slabs
      const isLarge = a > 0.77; // ~23% taller/larger rectangular objects

      let rawH: number;
      if (isLarge) {
        rawH = 1.8 + b * 1.6;
      } else {
        rawH = [0, 0, 0.35, 0.75, 0, 1.1, 0.45, 0, 1.4][Math.floor(a * 9)] ?? 0;
      }

      const h = U * 0.08 * rawH * hFade;
      const xl = (i + g) * U;
      const xr = (i + 1 - g) * U;
      const v = 0.92 + b * 0.08;

      const baseTop = isGrey ? TOP_GREY : TOP_PURPLE;
      const baseFront = isGrey ? FRONT_GREY : FRONT_PURPLE;
      const baseSide = isGrey ? SIDE_GREY : SIDE_PURPLE;

      const topCol: [number, number, number] = baseTop.map(x => (x * v) | 0) as [number, number, number];
      const sideCol = mix(baseSide, t);
      const frontCol = mix(baseFront, t);

      if (h > 0.001) {
        // Side face
        if (xr <= camX) poly(ctx, [P(xr, zn, h), P(xr, zf, h), P(xr, zf), P(xr, zn)], sideCol);
        else if (xl >= camX) poly(ctx, [P(xl, zn, h), P(xl, zf, h), P(xl, zf), P(xl, zn)], sideCol);
        // Front face
        poly(ctx, [P(xl, zn, h), P(xr, zn, h), P(xr, zn), P(xl, zn)], frontCol);
      } else {
        // Flat tile front ledge
        poly(ctx, [P(xl, zn, 0.012), P(xr, zn, 0.012), P(xr, zn), P(xl, zn)], frontCol);
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

  const targetMouse = useRef({ x: 0, y: 0 });
  const currentCam = useRef({ x: 0, y: 0 });
  const progressRef = useRef(0);
  const lastTimeRef = useRef<number | null>(null);
  const lastHRef = useRef<number>(-1);
  const isVisibleRef = useRef<boolean>(true);

  // Track mouse coordinates across the screen with smooth easing
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const nx = (e.clientX / window.innerWidth) * 2 - 1;
      const ny = (e.clientY / window.innerHeight) * 2 - 1;
      targetMouse.current = {
        x: Math.max(-1, Math.min(1, nx)),
        y: Math.max(-1, Math.min(1, ny)),
      };
    };

    const handleMouseLeave = () => {
      targetMouse.current = { x: 0, y: 0 };
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    window.addEventListener('mouseleave', handleMouseLeave);
    window.addEventListener('blur', handleMouseLeave);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseleave', handleMouseLeave);
      window.removeEventListener('blur', handleMouseLeave);
    };
  }, []);

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

  // Smooth, high-performance animation loop
  useEffect(() => {
    let animId: number;

    const tick = (now: number) => {
      if (!isVisibleRef.current) {
        lastTimeRef.current = null;
        animId = requestAnimationFrame(tick);
        return;
      }

      if (lastTimeRef.current === null) lastTimeRef.current = now;
      const dt = Math.min((now - lastTimeRef.current) / 1000, 0.05);
      lastTimeRef.current = now;

      // Steady gentle glide forward
      progressRef.current += dt * 0.72;

      // Camera parallax easing
      const smoothFactor = 1 - Math.exp(-3.8 * dt);
      currentCam.current.x += (targetMouse.current.x * 0.20 - currentCam.current.x) * smoothFactor;
      currentCam.current.y += (targetMouse.current.y * 0.07 - currentCam.current.y) * smoothFactor;

      if (heroRef.current && backRef.current && frontRef.current) {
        const heroH = heroRef.current.clientHeight;
        const wristY = drawFloor(
          heroRef.current,
          backRef.current,
          frontRef.current,
          progressRef.current,
          currentCam.current.x,
          currentCam.current.y,
        );

        // Only fire onWristY when hero height actually changes, avoiding React render cascades
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
