import React, { useEffect, useState } from 'react';

interface PramanaHeroHandsProps {
  /**
   * The Y pixel (within the hero section) where the hand wrists touch the floor.
   * Passed from VoxelFloorCanvas so the SVG is pinned precisely to the floor horizon.
   * If omitted the SVG aligns to the bottom of its container as before.
   */
  wristY?: number;
}

export const PramanaHeroHands: React.FC<PramanaHeroHandsProps> = ({ wristY }) => {
  const [mouseNorm, setMouseNorm] = useState({ x: 0, y: 0 });
  const [hoveredFinger, setHoveredFinger] = useState<string | null>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMouseNorm({
        x: Math.max(-1, Math.min(1, (e.clientX / window.innerWidth) * 2 - 1)),
        y: Math.max(-1, Math.min(1, (e.clientY / window.innerHeight) * 2 - 1)),
      });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  // ── Pupil offsets ──────────────────────────────────────────────────────────
  // Left (pink) hand: base gaze is right (+x) toward the purple hand
  const pinkPupilCx  = 288 + 6  + mouseNorm.x * 3;
  const pinkPupilCy  = 172 + 2  + mouseNorm.y * 2;

  // Right (purple) hand: rendered in a mirrored group, so we keep the same
  // base offset — the scale(-1) flip will naturally make it look left.
  const purplePupilCx = 288 + 6  + mouseNorm.x * 3;
  const purplePupilCy = 172 + 2  + mouseNorm.y * 2;

  // ── Finger scale helper ────────────────────────────────────────────────────
  const fingerStyle = (id: string): React.CSSProperties => ({
    transformBox: 'fill-box',
    transformOrigin: 'bottom center',
    transform: hoveredFinger === id ? 'scaleY(0.88)' : 'scaleY(1)',
    transition: 'transform 140ms ease',
  });

  // ── Inline hand renderer (used for both hands) ─────────────────────────────
  // skin / ring colours are passed so we can reuse JSX for both sides.
  const HandPaths = ({
    side,
    skin,
    ring,
    pupilCx,
    pupilCy,
  }: {
    side: 'left' | 'right';
    skin: string;
    ring: string;
    pupilCx: number;
    pupilCy: number;
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
          <circle cx="0" cy="-76" r="8" fill="#fff" />
        </g>
      </g>

      {/* ── Finger 2: ring ── translate(122,185) rotate(-7) */}
      <g transform="translate(122,185) rotate(-7)">
        <g
          className="pointer-events-auto cursor-pointer"
          style={fingerStyle(`${side}-2`)}
          onMouseEnter={() => setHoveredFinger(`${side}-2`)}
          onMouseLeave={() => setHoveredFinger(null)}
        >
          <rect x="-24" y="-140" width="48" height="165" rx="24" fill={skin} />
          <circle cx="0" cy="-116" r="8" fill="#FFD9B8" />
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
          <circle cx="0" cy="-136" r="8" fill="#D9CCF5" />
        </g>
      </g>

      {/* ── OK ring (stroke donut) ── */}
      <circle cx="268" cy="158" r="58" fill="none" stroke={ring} strokeWidth="26" />

      {/* ── Eye (sclera) ── */}
      <ellipse cx="272" cy="170" rx="40" ry="33" fill="#fff" />

      {/* ── Pupil + glint ── */}
      <ellipse
        cx={pupilCx}
        cy={pupilCy}
        rx="14"
        ry="16"
        fill="#111"
        style={{ transition: 'cx 180ms ease-out, cy 180ms ease-out' }}
      />
      <circle
        cx={pupilCx - 5}
        cy={pupilCy - 6}
        r="4.5"
        fill="#fff"
        style={{ transition: 'cx 180ms ease-out, cy 180ms ease-out' }}
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
      <circle cx="333" cy="168" r="7" fill="#fff" />
    </>
  );

  // The SVG viewBox is 723×382. The hand wrists end at y≈335 in SVG space.
  // wristY is relative to the top of the hero section (which is our absolute
  // positioning parent via "absolute inset-0" below).
  //
  // The SVG width is min(100vw, 723px). Its rendered height = width * (382/723).
  // The wrist sits at (335/382) of that height from the SVG top.
  // So:  top = wristY - svgWidth * (335/723)
  //
  // We can't know svgWidth in CSS without JS, but we CAN express this as:
  //   top = wristY px,  then use translateY to shift up by (335/382 * 100%)
  // where 100% refers to the SVG's own rendered height.
  const svgStyle: React.CSSProperties = wristY !== undefined
    ? {
        position: 'absolute',
        top: wristY,
        left: '63%',
        // shift left center, then shift up so SVG y=335 (88% down) aligns to top
        transform: 'translateX(-50%) translateY(-87.7%)',
        width: 'min(100%, 723px)',
        filter: 'drop-shadow(0 16px 32px rgba(0,0,0,0.10))',
        zIndex: 10,
      }
    : { filter: 'drop-shadow(0 16px 32px rgba(0,0,0,0.10))' };

  return (
    <div className="absolute inset-0 pointer-events-none select-none">
      <svg
        viewBox="0 0 723 382"
        xmlns="http://www.w3.org/2000/svg"
        className={wristY !== undefined ? 'overflow-visible' : 'w-full max-w-[680px] sm:max-w-[723px] h-auto overflow-visible'}
        style={svgStyle}
      >
        {/* ── LEFT HAND (pink) ─────────────────────────── */}
        <g>
          <HandPaths
            side="left"
            skin="#E4789A"
            ring="#D4688F"
            pupilCx={pinkPupilCx}
            pupilCy={pinkPupilCy}
          />
        </g>

        {/* ── RIGHT HAND (purple, mirrored) ─────────────── */}
        <g transform="translate(723,0) scale(-1,1)">
          <HandPaths
            side="right"
            skin="#7B3FF2"
            ring="#6A2FD8"
            pupilCx={purplePupilCx}
            pupilCy={purplePupilCy}
          />
        </g>
      </svg>
    </div>
  );
};
