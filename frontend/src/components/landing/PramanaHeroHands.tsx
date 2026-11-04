import React, { useEffect, useState, useRef } from 'react';

interface PramanaHeroHandsProps {
  /**
   * The Y pixel (within the hero section) where the hand wrists touch the floor.
   * Passed from VoxelFloorCanvas so the SVG is pinned precisely to the floor horizon.
   * If omitted the SVG aligns to the bottom of its container as before.
   */
  wristY?: number;
}

export const PramanaHeroHands: React.FC<PramanaHeroHandsProps> = ({ wristY }) => {
  const [hoveredFinger, setHoveredFinger] = useState<string | null>(null);

  // SVG group and element refs to animate directly on the DOM with ZERO React re-renders
  const pinkHandRef = useRef<SVGGElement>(null);
  const purpleHandRef = useRef<SVGGElement>(null);
  const pinkPupilRef = useRef<SVGEllipseElement>(null);
  const pinkGlintRef = useRef<SVGCircleElement>(null);
  const purplePupilRef = useRef<SVGEllipseElement>(null);
  const purpleGlintRef = useRef<SVGCircleElement>(null);

  const targetMouse = useRef({ x: 0, y: 0 });
  const currentGaze = useRef({ x: 0, y: 0 });
  const startTimeRef = useRef<number | null>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
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
      if (startTimeRef.current === null) startTimeRef.current = now;
      const elapsed = (now - startTimeRef.current) / 1000;

      const dt = Math.min((now - lastTime) / 1000, 0.05);
      lastTime = now;
      const t = now * 0.001;

      // Pop-out entrance animation: hands rocket out of the land box like a jack-in-the-box
      let popY = 0;
      if (elapsed < 1.4) {
        if (elapsed < 0.12) {
          popY = 320; // submerged deep inside the box
        } else {
          const p = Math.min(1, (elapsed - 0.12) / 0.65);
          const easeOut = Math.sin(p * Math.PI * 0.5);
          // Elastic spring bounce overshoot
          const bounce = Math.sin(p * Math.PI * 2.5) * Math.exp(-3.5 * p);
          popY = (1 - easeOut) * 320 - bounce * 55;
        }
      }

      // Exponential decay smoothing for gaze tracking (responsive & smooth)
      const gazeLerp = 1 - Math.exp(-14 * dt);
      currentGaze.current.x += (targetMouse.current.x - currentGaze.current.x) * gazeLerp;
      currentGaze.current.y += (targetMouse.current.y - currentGaze.current.y) * gazeLerp;

      const gx = currentGaze.current.x;
      const gy = currentGaze.current.y;

      // Gentle breathing float on the floor (blends in smoothly after pop-out)
      const leftY = Math.sin(t * 1.5) * 2.2;
      const leftRot = Math.cos(t * 1.1) * 0.45;
      const rightY = Math.sin(t * 1.5 + 1.2) * 2.5;
      const rightRot = Math.cos(t * 1.1 + 1.2) * 0.45;

      if (pinkHandRef.current) {
        pinkHandRef.current.setAttribute(
          'transform',
          `translate(0, ${(popY + leftY).toFixed(2)}) scale(1.04) rotate(${leftRot.toFixed(2)}, 160, 240)`
        );
      }
      if (purpleHandRef.current) {
        purpleHandRef.current.setAttribute(
          'transform',
          `translate(740, 18) scale(-0.92, 0.92) translate(0, ${(popY * 1.08 + rightY).toFixed(2)}) rotate(${rightRot.toFixed(2)}, 160, 240)`
        );
      }

      // Pink pupil: dynamic gaze actively following cursor across screen
      const pCx = 276 + gx * 16;
      const pCy = 170 + gy * 10;
      if (pinkPupilRef.current) {
        pinkPupilRef.current.setAttribute('cx', pCx.toFixed(1));
        pinkPupilRef.current.setAttribute('cy', pCy.toFixed(1));
      }
      if (pinkGlintRef.current) {
        pinkGlintRef.current.setAttribute('cx', (pCx - 5).toFixed(1));
        pinkGlintRef.current.setAttribute('cy', (pCy - 5).toFixed(1));
      }

      // Purple pupil: dynamic gaze actively following cursor across screen (mirrored coordinate space)
      const uCx = 272 - gx * 16;
      const uCy = 156 + gy * 10;
      if (purplePupilRef.current) {
        purplePupilRef.current.setAttribute('cx', uCx.toFixed(1));
        purplePupilRef.current.setAttribute('cy', uCy.toFixed(1));
      }
      if (purpleGlintRef.current) {
        purpleGlintRef.current.setAttribute('cx', (uCx - 4.5).toFixed(1));
        purpleGlintRef.current.setAttribute('cy', (uCy - 4.5).toFixed(1));
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

  // ── Finger scale helper ────────────────────────────────────────────────────
  const fingerStyle = (id: string): React.CSSProperties => ({
    transformBox: 'fill-box',
    transformOrigin: 'bottom center',
    transform: hoveredFinger === id ? 'scaleY(0.86)' : 'scaleY(1)',
    transition: 'transform 200ms cubic-bezier(0.34, 1.56, 0.64, 1)',
  });

  // ── Inline hand renderer (used for both hands) ─────────────────────────────
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
      {/* ── Finger 1: pinky ── translate(78,190) rotate(-14) */}
      <g transform="translate(78,190) rotate(-14)">
        <g
          className="pointer-events-auto cursor-pointer"
          style={fingerStyle(`${side}-1`)}
          onMouseEnter={() => setHoveredFinger(`${side}-1`)}
          onMouseLeave={() => setHoveredFinger(null)}
        >
          <rect x="-24" y="-100" width="48" height="125" rx="24" fill={skin} />
          <circle cx="0" cy="-76" r="8" fill="#ffffff" />
        </g>
      </g>

      {/* ── Finger 2: ring (with cute warm yellow dot accent from reference image) ── translate(122,185) rotate(-7) */}
      <g transform="translate(122,185) rotate(-7)">
        <g
          className="pointer-events-auto cursor-pointer"
          style={fingerStyle(`${side}-2`)}
          onMouseEnter={() => setHoveredFinger(`${side}-2`)}
          onMouseLeave={() => setHoveredFinger(null)}
        >
          <rect x="-24" y="-140" width="48" height="165" rx="24" fill={skin} />
          <circle cx="0" cy="-116" r="8" fill="#FEE08B" />
        </g>
      </g>

      {/* ── Finger 3: middle ── translate(162,180) rotate(-3) */}
      <g transform="translate(162,180) rotate(-3)">
        <g
          className="pointer-events-auto cursor-pointer"
          style={fingerStyle(`${side}-3`)}
          onMouseEnter={() => setHoveredFinger(`${side}-3`)}
          onMouseLeave={() => setHoveredFinger(null)}
        >
          <rect x="-24" y="-160" width="48" height="185" rx="24" fill={skin} />
          <circle cx="0" cy="-136" r="8" fill="#ffffff" />
        </g>
      </g>

      {/* ── OK ring (stroke donut) ── */}
      <circle cx="268" cy="158" r="58" fill="none" stroke={ring} strokeWidth="26" />

      {/* ── Eye (sclera) ── */}
      <ellipse cx="272" cy="170" rx="40" ry="33" fill="#ffffff" />

      {/* ── Pupil + glint (direct ref targets for 60fps zero-cost animation) ── */}
      <ellipse
        ref={pupilRef}
        cx={initialPupilCx}
        cy={initialPupilCy}
        rx="14"
        ry="16"
        fill="#111111"
      />
      <circle
        ref={glintRef}
        cx={initialPupilCx - 5}
        cy={initialPupilCy - 5}
        r="4.5"
        fill="#ffffff"
      />

      {/* ── Palm + thumb ── */}
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

      {/* White dot on ring outer edge */}
      <circle cx="333" cy="168" r="7.5" fill="#ffffff" />
    </>
  );

  const svgStyle: React.CSSProperties = {
    position: 'absolute',
    top: wristY !== undefined ? `${wristY}px` : '68.6%',
    left: '64%',
    transform: 'translateX(-50%) translateY(-87.7%)',
    width: 'min(100%, 730px)',
    filter: 'drop-shadow(0 18px 36px rgba(0,0,0,0.12))',
    zIndex: 10,
    willChange: 'transform',
  };

  return (
    <div className="absolute inset-0 pointer-events-none select-none">
      <svg
        viewBox="0 0 740 390"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full max-w-[660px] sm:max-w-[730px] h-auto overflow-visible"
        style={svgStyle}
      >
        {/* ── RIGHT HAND (purple, slightly smaller, sitting behind, character eyes looking UP) ── */}
        <g
          ref={purpleHandRef}
          transform="translate(740, 18) scale(-0.92, 0.92) translate(0, 0) rotate(0, 160, 240)"
        >
          <HandPaths
            side="right"
            skin="#703BE8"
            ring="#5E27D5"
            initialPupilCx={280}
            initialPupilCy={148}
            pupilRef={purplePupilRef}
            glintRef={purpleGlintRef}
          />
        </g>

        {/* ── LEFT HAND (pink, larger, closer to front, character eyes looking TO THE SIDE) ── */}
        <g
          ref={pinkHandRef}
          transform="translate(0, 0) scale(1.04) rotate(0, 160, 240)"
          filter="drop-shadow(6px 10px 20px rgba(0,0,0,0.15))"
        >
          <HandPaths
            side="left"
            skin="#EE738A"
            ring="#DB5B74"
            initialPupilCx={292}
            initialPupilCy={170}
            pupilRef={pinkPupilRef}
            glintRef={pinkGlintRef}
          />
        </g>
      </svg>
    </div>
  );
};
