import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  drawWholeHand,
  tapAngle,
  type HandPose,
  type Folds,
  CUT,
} from './hand';

interface PramanaHeroHandsProps {
  /**
   * The Y pixel (within the hero section) where the hand wrists touch the floor.
   * Passed from VoxelFloorCanvas so the hands are pinned precisely to the floor horizon.
   */
  wristY?: number;
}

export const PramanaHeroHands: React.FC<PramanaHeroHandsProps> = ({ wristY }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Interaction states
  const [hoveredHand, setHoveredHand] = useState<'left' | 'right' | null>(null);

  // Animation and state refs (kept out of React state for silky 60fps loop)
  const animFrameRef = useRef<number>(0);
  const pointerPos = useRef({ x: 0, y: 0, has: false });

  // Gaze tracking for Rose (left) and Violet (right)
  const gazeLeft = useRef({ px: 0, py: 0 });
  const gazeRight = useRef({ px: 0, py: 0 });

  // Blinking states
  const blinkLeft = useRef({ start: 0, duration: 160, isBlinking: false });
  const blinkRight = useRef({ start: 0, duration: 160, isBlinking: false });
  const nextBlinkLeft = useRef(performance.now() + 2500);
  const nextBlinkRight = useRef(performance.now() + 3200);

  // Tapping states (triggering tapAngle)
  const tapLeftStart = useRef<number>(-9999);
  const tapRightStart = useRef<number>(-9999);
  const nextTapSchedule = useRef(performance.now() + 3500);
  const tapTurn = useRef<'left' | 'right'>('left');

  // Finger fold animation targets (for hover)
  const foldLeft = useRef<[number, number, number]>([0, 0, 0]);
  const foldRight = useRef<[number, number, number]>([0, 0, 0]);

  // Trigger manual blink
  const triggerBlink = useCallback(() => {
    const now = performance.now();
    blinkLeft.current = { start: now, duration: 160, isBlinking: true };
    blinkRight.current = { start: now, duration: 160, isBlinking: true };
  }, []);

  // Trigger manual tap
  const triggerTap = useCallback((side: 'left' | 'right') => {
    const now = performance.now();
    if (side === 'left') {
      tapLeftStart.current = now;
    } else {
      tapRightStart.current = now;
    }
  }, []);

  // Click handler on hands container
  const handlePointerDown = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    triggerBlink();
    const rect = canvasRef.current?.getBoundingClientRect();
    if (rect) {
      const clickX = e.clientX - rect.left;
      if (clickX < rect.width * 0.5) {
        triggerTap('left');
      } else {
        triggerTap('right');
      }
    }
  }, [triggerBlink, triggerTap]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const prefersReducedMotion =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Window mouse move listener to track gaze across the entire hero / page
    const handleWindowPointerMove = (e: PointerEvent) => {
      pointerPos.current = {
        x: e.clientX,
        y: e.clientY,
        has: true,
      };
    };

    const handleWindowPointerLeave = () => {
      pointerPos.current.has = false;
    };

    window.addEventListener('pointermove', handleWindowPointerMove, { passive: true });
    document.addEventListener('pointerleave', handleWindowPointerLeave);

    // Canvas coordinate dimensions (virtual resolution)
    const V_WIDTH = 640;
    const V_HEIGHT = 440;

    let lastTime = performance.now();

    const render = (now: number) => {
      const dt = Math.min((now - lastTime) / 1000, 0.05);
      lastTime = now;
      const t = now * 0.001;

      // Handle DPI and canvas resizing
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const displayW = Math.round(rect.width * dpr);
      const displayH = Math.round(rect.height * dpr);

      if (canvas.width !== displayW || canvas.height !== displayH) {
        canvas.width = displayW;
        canvas.height = displayH;
      }

      ctx.save();
      ctx.scale(displayW / V_WIDTH, displayH / V_HEIGHT);
      ctx.clearRect(0, 0, V_WIDTH, V_HEIGHT);

      if (prefersReducedMotion) {
        // Static dignified still frame for reduced motion
        const stillLeft: HandPose = {
          hue: 'rose',
          mirror: true,
          pose: 0,
          tapDeg: 0,
          folds: [0, 0, 0],
          tilt: 0,
          eye: { px: 0, py: 0, open: 1 },
        };
        const stillRight: HandPose = {
          hue: 'violet',
          mirror: false,
          pose: 0,
          tapDeg: 0,
          folds: [0, 0, 0],
          tilt: 0,
          eye: { px: 0, py: 0, open: 1 },
        };

        // Draw left hand (Rose)
        ctx.save();
        ctx.translate(30, 42);
        ctx.scale(0.84, 0.84);
        drawWholeHand(ctx, stillLeft, CUT + 45);
        ctx.restore();

        // Draw right hand (Violet)
        ctx.save();
        ctx.translate(345, 68);
        ctx.scale(0.77, 0.77);
        drawWholeHand(ctx, stillRight, CUT + 45);
        ctx.restore();

        ctx.restore();
        return;
      }

      // ── 1. Automatic periodic tapping ──
      if (now > nextTapSchedule.current) {
        if (tapTurn.current === 'left') {
          tapLeftStart.current = now;
          tapTurn.current = 'right';
          nextTapSchedule.current = now + 4200;
        } else {
          tapRightStart.current = now;
          tapTurn.current = 'left';
          nextTapSchedule.current = now + 4800;
        }
      }

      const tapDegLeft = tapAngle(now - tapLeftStart.current);
      const tapDegRight = tapAngle(now - tapRightStart.current);

      // ── 2. Automatic natural blinking ──
      if (now > nextBlinkLeft.current && !blinkLeft.current.isBlinking) {
        blinkLeft.current = { start: now, duration: 150, isBlinking: true };
        nextBlinkLeft.current = now + 3200 + Math.random() * 3000;
      }
      if (now > nextBlinkRight.current && !blinkRight.current.isBlinking) {
        blinkRight.current = { start: now, duration: 150, isBlinking: true };
        nextBlinkRight.current = now + 3400 + Math.random() * 2800;
      }

      const computeBlinkOpen = (blink: { start: number; duration: number; isBlinking: boolean }) => {
        if (!blink.isBlinking) return 1;
        const u = (now - blink.start) / blink.duration;
        if (u >= 1) {
          blink.isBlinking = false;
          return 1;
        }
        if (u < 0.4) {
          return 1 - (u / 0.4) * 0.95;
        } else {
          return 0.05 + ((u - 0.4) / 0.6) * 0.95;
        }
      };

      const eyeOpenLeft = computeBlinkOpen(blinkLeft.current);
      const eyeOpenRight = computeBlinkOpen(blinkRight.current);

      // ── 3. Smooth Gaze Tracking ──
      let targetLeftPx = 0;
      let targetLeftPy = 0;
      let targetRightPx = 0;
      let targetRightPy = 0;

      if (pointerPos.current.has) {
        // Left eye center in screen coordinates
        const scaleX = rect.width / V_WIDTH;
        const scaleY = rect.height / V_HEIGHT;

        // Rose hand eye screen coord: (30 + (360 - 112) * 0.84, 42 + 222 * 0.84)
        const eyeLeftScreenX = rect.left + (30 + 248 * 0.84) * scaleX;
        const eyeLeftScreenY = rect.top + (42 + 222 * 0.84) * scaleY;

        // Violet hand eye screen coord: (345 + 112 * 0.77, 68 + 222 * 0.77)
        const eyeRightScreenX = rect.left + (345 + 112 * 0.77) * scaleX;
        const eyeRightScreenY = rect.top + (68 + 222 * 0.77) * scaleY;

        const dLx = pointerPos.current.x - eyeLeftScreenX;
        const dLy = pointerPos.current.y - eyeLeftScreenY;
        const distL = Math.hypot(dLx, dLy) + 120;
        targetLeftPx = Math.max(-12, Math.min(12, (dLx / distL) * 16));
        targetLeftPy = Math.max(-8, Math.min(8, (dLy / distL) * 12));

        const dRx = pointerPos.current.x - eyeRightScreenX;
        const dRy = pointerPos.current.y - eyeRightScreenY;
        const distR = Math.hypot(dRx, dRy) + 120;
        targetRightPx = Math.max(-12, Math.min(12, (dRx / distR) * 16));
        targetRightPy = Math.max(-8, Math.min(8, (dRy / distR) * 12));
      }

      // Exponential smoothing for natural gaze
      const gazeLerp = 1 - Math.exp(-12 * dt);
      gazeLeft.current.px += (targetLeftPx - gazeLeft.current.px) * gazeLerp;
      gazeLeft.current.py += (targetLeftPy - gazeLeft.current.py) * gazeLerp;
      gazeRight.current.px += (targetRightPx - gazeRight.current.px) * gazeLerp;
      gazeRight.current.py += (targetRightPy - gazeRight.current.py) * gazeLerp;

      // ── 4. Interactive Finger Folds (Hover Curl) ──
      const targetFoldLeft: [number, number, number] =
        hoveredHand === 'left' ? [0.45, 0.65, 0.5] : [0, 0, 0];
      const targetFoldRight: [number, number, number] =
        hoveredHand === 'right' ? [0.45, 0.65, 0.5] : [0, 0, 0];

      const foldLerp = 1 - Math.exp(-8 * dt);
      for (let k = 0; k < 3; k++) {
        foldLeft.current[k] += (targetFoldLeft[k] - foldLeft.current[k]) * foldLerp;
        foldRight.current[k] += (targetFoldRight[k] - foldRight.current[k]) * foldLerp;
      }

      // ── 5. Idle Bobbing & Tilting ──
      const bobLeft = Math.sin(t * 1.5) * 4.5;
      const bobRight = Math.sin(t * 1.5 + 1.2) * 4.0;
      const tiltLeft = Math.sin(t * 1.2) * 2.2 + gazeLeft.current.px * 0.15;
      const tiltRight = Math.sin(t * 1.2 + 0.9) * -2.4 + gazeRight.current.px * 0.15;

      // ── 6. Assemble Hand Poses ──
      const poseLeft: HandPose = {
        hue: 'rose',
        mirror: true, // OK ring faces toward the purple hand
        pose: 0,
        tapDeg: tapDegLeft,
        folds: foldLeft.current as Folds,
        tilt: tiltLeft,
        eye: {
          px: gazeLeft.current.px,
          py: gazeLeft.current.py,
          open: eyeOpenLeft,
        },
      };

      const poseRight: HandPose = {
        hue: 'violet',
        mirror: false, // OK ring faces toward the pink hand
        pose: 0,
        tapDeg: tapDegRight,
        folds: foldRight.current as Folds,
        tilt: tiltRight,
        eye: {
          px: gazeRight.current.px,
          py: gazeRight.current.py,
          open: eyeOpenRight,
        },
      };

      // ── 7. Draw Hands onto Canvas ──
      // Hand 1: Rose (Pink) on the left
      ctx.save();
      ctx.translate(30, 42 + bobLeft);
      ctx.scale(0.84, 0.84);
      drawWholeHand(ctx, poseLeft, CUT + 45);
      ctx.restore();

      // Hand 2: Violet (Purple) on the right
      ctx.save();
      ctx.translate(345, 68 + bobRight);
      ctx.scale(0.77, 0.77);
      drawWholeHand(ctx, poseRight, CUT + 45);
      ctx.restore();

      ctx.restore();
      animFrameRef.current = requestAnimationFrame(render);
    };

    animFrameRef.current = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animFrameRef.current);
      window.removeEventListener('pointermove', handleWindowPointerMove);
      document.removeEventListener('pointerleave', handleWindowPointerLeave);
    };
  }, [hoveredHand]);

  // Handle pointer hover on hands
  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = e.clientX - rect.left;
    if (x < rect.width * 0.48) {
      setHoveredHand('left');
    } else {
      setHoveredHand('right');
    }
  };

  const handlePointerLeave = () => {
    setHoveredHand(null);
  };

  return (
    <div className="absolute inset-0 pointer-events-none select-none z-10 overflow-visible">
      <div
        ref={containerRef}
        onPointerMove={handlePointerMove}
        onPointerLeave={handlePointerLeave}
        onPointerDown={handlePointerDown}
        className="pointer-events-auto cursor-pointer absolute left-1/2 lg:left-[69%] xl:left-[70%] -translate-x-1/2 w-[min(92vw,500px)] lg:w-[min(42vw,580px)] h-auto overflow-visible select-none"
        style={{
          top: wristY !== undefined ? `${wristY}px` : '70%',
          transform: 'translateX(-50%) translateY(-86%)',
          filter: 'drop-shadow(0 20px 36px rgba(45, 10, 80, 0.14))',
          willChange: 'transform',
        }}
        title="Interactive Pramana hand verifiers: click or hover to interact"
      >
        <canvas
          ref={canvasRef}
          className="w-full h-auto block overflow-visible"
          style={{
            aspectRatio: '640 / 440',
          }}
          aria-label="Two hands, one rose and one violet, making OK signs around watching eyes that track your cursor and confirm approvals"
        />
      </div>
    </div>
  );
};
