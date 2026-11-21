import React, { useEffect, useState, useRef } from 'react';
import { LANDING_PALETTE } from '../../landing/palette';

interface PramanaHeroHandsProps {
  /**
   * The Y pixel (within the hero section) where the hand wrists touch the floor.
   * Passed from VoxelFloorCanvas so the SVG is pinned precisely to the floor horizon.
   */
  wristY?: number;
}

export const PramanaHeroHands: React.FC<PramanaHeroHandsProps> = ({ wristY }) => {
  const [hoveredFinger, setHoveredFinger] = useState<string | null>(null);

  // SVG group and element refs for 60fps transform updates with 0 React re-renders
  const pinkHandRef = useRef<SVGGElement>(null);
  const purpleHandRef = useRef<SVGGElement>(null);
  const pinkPupilRef = useRef<SVGEllipseElement>(null);
  const pinkGlintRef = useRef<SVGCircleElement>(null);
  const purplePupilRef = useRef<SVGEllipseElement>(null);
  const purpleGlintRef = useRef<SVGCircleElement>(null);

  const targetMouse = useRef({ x: 0, y: 0 });
  const currentGaze = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const prefersReducedMotion =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const handleMouseMove = (e: MouseEvent) => {
      if (prefersReducedMotion) return;
      targetMouse.current = {
        x: Math.max(-1, Math.min(1, (e.clientX / window.innerWidth) * 2 - 1)),
        y: Math.max(-1, Math.min(1, (e.clientY / window.innerHeight) * 2 - 1)),
      };
    };

    const handleMouseLeave = () => {
      targetMouse.current = { x: 0, y: 0 };
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    window.addEventListener('mouseleave', handleMouseLeave);
    window.addEventListener('blur', handleMouseLeave);

    let animId: number;
    let lastTime = performance.now();

    const animate = (now: number) => {
      const dt = Math.min((now - lastTime) / 1000, 0.05);
      lastTime = now;
      const t = now * 0.001;

      if (!prefersReducedMotion) {
        // Smooth exponential damping for subtle gaze tracking
        const gazeLerp = 1 - Math.exp(-10 * dt);
        currentGaze.current.x += (targetMouse.current.x - currentGaze.current.x) * gazeLerp;
        currentGaze.current.y += (targetMouse.current.y - currentGaze.current.y) * gazeLerp;

        const gx = currentGaze.current.x;
        const gy = currentGaze.current.y;

        // Very subtle idle breathing movement (visually stable, no wild bouncing)
        const leftY = Math.sin(t * 1.2) * 1.2;
        const rightY = Math.sin(t * 1.2 + 1.1) * 1.4;

        if (pinkHandRef.current) {
          pinkHandRef.current.setAttribute(
            'transform',
            `translate(10, ${leftY.toFixed(2)}) scale(0.86)`
          );
        }
        if (purpleHandRef.current) {
          purpleHandRef.current.setAttribute(
            'transform',
            `translate(580, 28) scale(-0.76, 0.76) translate(0, ${rightY.toFixed(2)})`
          );
        }

        // Pink pupil: subtle eye tracking
        const pCx = 284 + gx * 8;
        const pCy = 170 + gy * 5;
        if (pinkPupilRef.current) {
          pinkPupilRef.current.setAttribute('cx', pCx.toFixed(1));
          pinkPupilRef.current.setAttribute('cy', pCy.toFixed(1));
        }
        if (pinkGlintRef.current) {
          pinkGlintRef.current.setAttribute('cx', (pCx - 3.5).toFixed(1));
          pinkGlintRef.current.setAttribute('cy', (pCy - 3.5).toFixed(1));
        }

        // Purple pupil: subtle eye tracking (mirrored space)
        const uCx = 284 - gx * 8;
        const uCy = 154 + gy * 5;
        if (purplePupilRef.current) {
          purplePupilRef.current.setAttribute('cx', uCx.toFixed(1));
          purplePupilRef.current.setAttribute('cy', uCy.toFixed(1));
        }
        if (purpleGlintRef.current) {
          purpleGlintRef.current.setAttribute('cx', (uCx - 3.5).toFixed(1));
          purpleGlintRef.current.setAttribute('cy', (uCy - 3.5).toFixed(1));
        }
      }

      animId = requestAnimationFrame(animate);
    };

    animId = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseleave', handleMouseLeave);
      window.removeEventListener('blur', handleMouseLeave);
      cancelAnimationFrame(animId);
    };
  }, []);

  // ── Finger hover scale ──
  const fingerStyle = (id: string): React.CSSProperties => ({
    transformBox: 'fill-box',
    transformOrigin: 'bottom center',
    transform: hoveredFinger === id ? 'scaleY(0.88)' : 'scaleY(1)',
    transition: 'transform 200ms cubic-bezier(0.34, 1.56, 0.64, 1)',
  });

  // ── Hand SVG Paths ──
  const HandPaths = ({
    side,
    skin,
    ring,
    initialPupilCx,
    initialPupilCy,
    pupilRef,
    glintRef,
  }: {
    side: 'left' | 'right';
    skin: string;
    ring: string;
    initialPupilCx: number;
    initialPupilCy: number;
    pupilRef: React.RefObject<SVGEllipseElement | null>;
    glintRef: React.RefObject<SVGCircleElement | null>;
  }) => (
    <>
      {/* Finger 1: pinky */}
      <g transform="translate(78,190) rotate(-14)">
        <g
          className="pointer-events-auto cursor-pointer"
          style={fingerStyle(`${side}-1`)}
          onMouseEnter={() => setHoveredFinger(`${side}-1`)}
          onMouseLeave={() => setHoveredFinger(null)}
        >
          <rect x="-24" y="-100" width="48" height="125" rx="24" fill={skin} />
          <circle cx="0" cy="-76" r="8" fill="#FFFFFF" />
        </g>
      </g>

      {/* Finger 2: ring (with signature warm yellow dot accent) */}
      <g transform="translate(122,185) rotate(-7)">
        <g
          className="pointer-events-auto cursor-pointer"
          style={fingerStyle(`${side}-2`)}
          onMouseEnter={() => setHoveredFinger(`${side}-2`)}
          onMouseLeave={() => setHoveredFinger(null)}
        >
          <rect x="-24" y="-140" width="48" height="165" rx="24" fill={skin} />
          <circle cx="0" cy="-116" r="8" fill={LANDING_PALETTE.characters.pink.ringFingerDot} />
        </g>
      </g>

      {/* Finger 3: middle (tallest) */}
      <g transform="translate(162,180) rotate(-3)">
        <g
          className="pointer-events-auto cursor-pointer"
          style={fingerStyle(`${side}-3`)}
          onMouseEnter={() => setHoveredFinger(`${side}-3`)}
          onMouseLeave={() => setHoveredFinger(null)}
        >
          <rect x="-24" y="-160" width="48" height="185" rx="24" fill={skin} />
          <circle cx="0" cy="-136" r="8" fill="#FFFFFF" />
        </g>
      </g>

      {/* "OK" Ring */}
      <circle cx="268" cy="158" r="58" fill="none" stroke={ring} strokeWidth="26" />

      {/* Sclera */}
      <ellipse cx="272" cy="170" rx="40" ry="33" fill="#FFFFFF" />

      {/* Pupil + Glint */}
      <ellipse
        ref={pupilRef}
        cx={initialPupilCx}
        cy={initialPupilCy}
        rx="13"
        ry="15"
        fill={LANDING_PALETTE.characters.pink.pupil}
      />
      <circle
        ref={glintRef}
        cx={initialPupilCx - 4}
        cy={initialPupilCy - 4}
        r="4"
        fill="#FFFFFF"
      />

      {/* Palm + Thumb */}
      <path
        d="M62 185 Q62 168 90 168 L190 168 Q235 175 245 215 L250 335 L62 335 Z"
        fill={skin}
      />
      <path
        d="M232 240 C275 252 315 232 326 190"
        fill="none"
        stroke={skin}
        strokeWidth="46"
        strokeLinecap="round"
      />

      {/* White dot accent on ring edge */}
      <circle cx="333" cy="168" r="7" fill="#FFFFFF" />
    </>
  );

  return (
    <div className="absolute inset-0 pointer-events-none select-none z-10">
      <div
        className="absolute left-1/2 lg:left-[69%] xl:left-[70%] -translate-x-1/2 w-[min(90vw,480px)] lg:w-[min(40vw,540px)] h-auto overflow-visible"
        style={{
          top: wristY !== undefined ? `${wristY}px` : '70%',
          transform: 'translateX(-50%) translateY(-86%)',
          filter: 'drop-shadow(0 16px 32px rgba(45, 10, 80, 0.12))',
          willChange: 'transform',
        }}
      >
        <svg
          viewBox="0 0 620 380"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-auto overflow-visible"
        >
          {/* ── RIGHT HAND (purple, slightly smaller, facing pink hand) ── */}
          <g
            ref={purpleHandRef}
            transform="translate(580, 28) scale(-0.76, 0.76)"
          >
            <HandPaths
              side="right"
              skin={LANDING_PALETTE.characters.purple.skin}
              ring={LANDING_PALETTE.characters.purple.ring}
              initialPupilCx={284}
              initialPupilCy={154}
              pupilRef={purplePupilRef}
              glintRef={purpleGlintRef}
            />
          </g>

          {/* ── LEFT HAND (pink, iconic OK gesture with playful eye) ── */}
          <g
            ref={pinkHandRef}
            transform="translate(10, 0) scale(0.86)"
            filter="drop-shadow(4px 8px 16px rgba(0,0,0,0.12))"
          >
            <HandPaths
              side="left"
              skin={LANDING_PALETTE.characters.pink.skin}
              ring={LANDING_PALETTE.characters.pink.ring}
              initialPupilCx={284}
              initialPupilCy={170}
              pupilRef={pinkPupilRef}
              glintRef={pinkGlintRef}
            />
          </g>
        </svg>
      </div>
    </div>
  );
};
