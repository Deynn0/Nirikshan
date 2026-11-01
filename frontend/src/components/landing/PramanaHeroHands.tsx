import React, { useEffect, useState } from 'react';

export const PramanaHeroHands: React.FC = () => {
  // Mouse tracking for gaze shift
  const [mouseNorm, setMouseNorm] = useState({ x: 0, y: 0 });
  const [hoveredFinger, setHoveredFinger] = useState<string | null>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const nx = (e.clientX / window.innerWidth) * 2 - 1;
      const ny = (e.clientY / window.innerHeight) * 2 - 1;
      setMouseNorm({
        x: Math.max(-1, Math.min(1, nx)),
        y: Math.max(-1, Math.min(1, ny)),
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  // Left hand pupil offset:
  // Base: looks RIGHT (+8px) toward purple hand and slightly DOWN (+2px)
  let pinkShiftX = mouseNorm.x * 2.5;
  let pinkShiftY = mouseNorm.y * 1.8;

  if (hoveredFinger === 'left-1') {
    pinkShiftX -= 4.0;
    pinkShiftY -= 2.0;
  } else if (hoveredFinger === 'left-2') {
    pinkShiftX -= 6.0;
    pinkShiftY -= 1.0;
  } else if (hoveredFinger === 'left-3') {
    pinkShiftX -= 8.0;
    pinkShiftY += 1.0;
  }

  // Right hand pupil offset:
  // Base: looks LEFT (-8px) toward pink hand and slightly DOWN (+2px)
  let purpleShiftX = mouseNorm.x * 2.5;
  let purpleShiftY = mouseNorm.y * 1.8;

  if (hoveredFinger === 'right-1') {
    purpleShiftX += 4.0;
    purpleShiftY -= 2.0;
  } else if (hoveredFinger === 'right-2') {
    purpleShiftX += 6.0;
    purpleShiftY -= 1.0;
  } else if (hoveredFinger === 'right-3') {
    purpleShiftX += 8.0;
    purpleShiftY += 1.0;
  }

  // Helper to render individual 3D foreground tiles overlapping the wrist
  const renderForegroundTile = (
    key: string,
    cx: number,
    cy: number,
    w: number,
    h: number
  ) => {
    const halfW = w / 2;
    const depth = 7;
    return (
      <g key={key} className="pointer-events-none">
        {/* Front face (darker purple #8E76E0) */}
        <polygon
          points={`${cx - halfW},${cy - h} ${cx + halfW},${cy - h} ${cx + halfW},${cy} ${cx - halfW},${cy}`}
          fill="#8E76E0"
        />
        {/* Top face (light purple #B7A2F0) */}
        <polygon
          points={`${cx},${cy - h - depth} ${cx + halfW},${cy - h} ${cx},${cy - h + depth * 0.4} ${cx - halfW},${cy - h}`}
          fill="#B7A2F0"
        />
        {/* Right side depth shadow (#7A62CE) */}
        <polygon
          points={`${cx + halfW},${cy - h} ${cx + halfW + 3},${cy - h - depth * 0.4} ${cx + halfW + 3},${cy - depth * 0.4} ${cx + halfW},${cy}`}
          fill="#7A62CE"
        />
      </g>
    );
  };

  return (
    <div className="relative w-full h-full flex items-end justify-center pointer-events-none select-none">
      {/* 
        Two Tall Upright Hand Characters matching the reference design:
        - Height ~320-340px, pair spans ~38-42% of hero width
        - LEFT hand (Pink #E4789A): 3 upright thick pill fingers on left leaning slightly left, 
          clear circular ring (darker pink #D4678C) on right around large eyeball looking right.
        - RIGHT hand (Purple #7B3FF2): mirrored, ring on left with eye looking left, 3 fingers on right.
        - Wrist goes straight down into the floor, with 6 individual 3D tiles overlapping the wrist base.
        - No pedestal, no flat slab, no skirt.
        - Individual fingers shrink to scaleY(0.6) on hover with dot moving with the finger.
      */}
      <div className="relative z-20 flex items-end justify-center gap-3 sm:gap-6 lg:gap-8 mb-[-4px]">
        {/* ========================================================= */}
        {/* LEFT HAND (Pink #E4789A) */}
        {/* ========================================================= */}
        <div className="relative flex flex-col items-center">
          <svg
            viewBox="0 0 280 340"
            fill="none"
            className="w-[215px] sm:w-[250px] md:w-[275px] lg:w-[295px] xl:w-[320px] h-auto overflow-visible filter drop-shadow-[0_12px_24px_rgba(228,120,154,0.18)]"
          >
            <g className="hand hand-left">
              {/* 1. Wrist/Forearm going straight down into the floor */}
              <rect
                className="wrist"
                x="44"
                y="190"
                width="122"
                height="150"
                rx="8"
                fill="#E4789A"
              />

              {/* 2. Palm connecting wrist, fingers and the ring */}
              <path
                className="palm"
                d="M 44 200 C 30 185 18 175 20 160 C 22 145 36 142 50 145 L 140 145 C 152 145 160 152 165 165 C 170 178 168 190 166 200 Z"
                fill="#E4789A"
              />
              <path
                d="M 40 185 C 20 175 16 160 20 145 L 148 145 C 160 145 174 165 174 195 L 40 195 Z"
                fill="#E4789A"
              />

              {/* 3. Three Fingers on the Left (Pinky shortest, Ring, Middle tallest) */}
              {/* Pinky: shortest, leaning left (~ -9°) */}
              <g transform="rotate(-9 38 195)">
                <g
                  id="left-finger-3"
                  className="finger finger-3"
                  onMouseEnter={() => setHoveredFinger('left-3')}
                  onMouseLeave={() => setHoveredFinger(null)}
                >
                  <rect
                    x="22"
                    y="85"
                    width="32"
                    height="110"
                    rx="16"
                    fill="#E4789A"
                  />
                  {/* Pastel white dot near tip */}
                  <circle cx="38" cy="103" r="4.5" fill="#FFFFFF" />
                </g>
              </g>

              {/* Ring finger: middle height, leaning slightly left (~ -4.5°) */}
              <g transform="rotate(-4.5 82 195)">
                <g
                  id="left-finger-2"
                  className="finger finger-2"
                  onMouseEnter={() => setHoveredFinger('left-2')}
                  onMouseLeave={() => setHoveredFinger(null)}
                >
                  <rect
                    x="66"
                    y="50"
                    width="32"
                    height="145"
                    rx="16"
                    fill="#E4789A"
                  />
                  {/* Pastel white dot near tip */}
                  <circle cx="82" cy="68" r="4.5" fill="#FFFFFF" />
                </g>
              </g>

              {/* Middle finger: tallest, upright (~ -1°) */}
              <g transform="rotate(-1 126.5 195)">
                <g
                  id="left-finger-1"
                  className="finger finger-1"
                  onMouseEnter={() => setHoveredFinger('left-1')}
                  onMouseLeave={() => setHoveredFinger(null)}
                >
                  <rect
                    x="110"
                    y="16"
                    width="33"
                    height="180"
                    rx="16.5"
                    fill="#E4789A"
                  />
                  {/* Pastel white dot near tip */}
                  <circle cx="126.5" cy="34" r="4.5" fill="#FFFFFF" />
                </g>
              </g>

              {/* 4. Large Eyeball inside the ring opening */}
              <g className="eye">
                {/* Sclera: big white circle */}
                <circle cx="195" cy="158" r="26.5" fill="#FFFFFF" />

                {/* Black pupil: looks right toward purple hand and slightly down */}
                <ellipse
                  cx={195 + 8 + pinkShiftX}
                  cy={158 + 2 + pinkShiftY}
                  rx="12"
                  ry="13.5"
                  fill="#18181B"
                  style={{ transition: 'cx 200ms ease-out, cy 200ms ease-out' }}
                />

                {/* Tiny glint highlight */}
                <circle
                  cx={195 + 8 + pinkShiftX - 4}
                  cy={158 + 2 + pinkShiftY - 4}
                  r="3.5"
                  fill="#FFFFFF"
                  style={{ transition: 'cx 200ms ease-out, cy 200ms ease-out' }}
                />
              </g>

              {/* 5. Clear "OK" Ring (donut shape, darker pink #D4678C) */}
              <g className="ring pointer-events-none">
                <path
                  d="M 195 112 A 46 46 0 1 0 195 204 A 46 46 0 1 0 195 112 Z M 195 133 A 25 25 0 1 0 195 183 A 25 25 0 1 0 195 133 Z"
                  fill="#D4678C"
                  fillRule="evenodd"
                />
                {/* Pastel white dot on outer edge of ring */}
                <circle cx="237" cy="158" r="4.5" fill="#FFFFFF" />
              </g>

              {/* 6. Foreground Tiles Overlapping the Wrist Base */}
              <g className="foreground-tiles">
                {renderForegroundTile('lt-1', 42, 330, 24, 14)}
                {renderForegroundTile('lt-2', 68, 334, 26, 8)}
                {renderForegroundTile('lt-3', 95, 326, 26, 18)}
                {renderForegroundTile('lt-4', 122, 331, 25, 11)}
                {renderForegroundTile('lt-5', 148, 327, 26, 16)}
                {renderForegroundTile('lt-6', 174, 333, 24, 8)}
              </g>
            </g>
          </svg>
        </div>

        {/* ========================================================= */}
        {/* RIGHT HAND (Purple #7B3FF2) */}
        {/* ========================================================= */}
        <div className="relative flex flex-col items-center">
          <svg
            viewBox="0 0 280 340"
            fill="none"
            className="w-[215px] sm:w-[250px] md:w-[275px] lg:w-[295px] xl:w-[320px] h-auto overflow-visible filter drop-shadow-[0_12px_24px_rgba(123,63,242,0.2)]"
          >
            <g className="hand hand-right">
              {/* 1. Wrist/Forearm going straight down into the floor */}
              <rect
                className="wrist"
                x="114"
                y="190"
                width="122"
                height="150"
                rx="8"
                fill="#7B3FF2"
              />

              {/* 2. Palm connecting wrist, ring and fingers */}
              <path
                className="palm"
                d="M 236 200 C 250 185 262 175 260 160 C 258 145 244 142 230 145 L 140 145 C 128 145 120 152 115 165 C 110 178 112 190 114 200 Z"
                fill="#7B3FF2"
              />
              <path
                d="M 240 185 C 260 175 264 160 260 145 L 132 145 C 120 145 106 165 106 195 L 240 195 Z"
                fill="#7B3FF2"
              />

              {/* 3. Large Eyeball inside the ring opening */}
              <g className="eye">
                {/* Sclera: big white circle */}
                <circle cx="85" cy="158" r="26.5" fill="#FFFFFF" />

                {/* Black pupil: looks left toward pink hand and slightly down */}
                <ellipse
                  cx={85 - 8 + purpleShiftX}
                  cy={158 + 2 + purpleShiftY}
                  rx="12"
                  ry="13.5"
                  fill="#18181B"
                  style={{ transition: 'cx 200ms ease-out, cy 200ms ease-out' }}
                />

                {/* Tiny glint highlight */}
                <circle
                  cx={85 - 8 + purpleShiftX - 4}
                  cy={158 + 2 + purpleShiftY - 4}
                  r="3.5"
                  fill="#FFFFFF"
                  style={{ transition: 'cx 200ms ease-out, cy 200ms ease-out' }}
                />
              </g>

              {/* 4. Clear "OK" Ring on the Left (darker purple #6F35DC) */}
              <g className="ring pointer-events-none">
                <path
                  d="M 85 112 A 46 46 0 1 0 85 204 A 46 46 0 1 0 85 112 Z M 85 133 A 25 25 0 1 0 85 183 A 25 25 0 1 0 85 133 Z"
                  fill="#6F35DC"
                  fillRule="evenodd"
                />
                {/* Pastel white dot on outer edge of ring */}
                <circle cx="43" cy="158" r="4.5" fill="#FFFFFF" />
              </g>

              {/* 5. Three Fingers on the Right (Middle tallest, Ring, Pinky shortest) */}
              {/* Middle finger: tallest, upright (~ +1°) */}
              <g transform="rotate(1 153.5 195)">
                <g
                  id="right-finger-1"
                  className="finger finger-1"
                  onMouseEnter={() => setHoveredFinger('right-1')}
                  onMouseLeave={() => setHoveredFinger(null)}
                >
                  <rect
                    x="137"
                    y="16"
                    width="33"
                    height="180"
                    rx="16.5"
                    fill="#7B3FF2"
                  />
                  {/* Pastel white dot near tip */}
                  <circle cx="153.5" cy="34" r="4.5" fill="#FFFFFF" />
                </g>
              </g>

              {/* Ring finger: middle height, leaning slightly right (~ +4.5°) */}
              <g transform="rotate(4.5 198 195)">
                <g
                  id="right-finger-2"
                  className="finger finger-2"
                  onMouseEnter={() => setHoveredFinger('right-2')}
                  onMouseLeave={() => setHoveredFinger(null)}
                >
                  <rect
                    x="182"
                    y="50"
                    width="32"
                    height="145"
                    rx="16"
                    fill="#7B3FF2"
                  />
                  {/* Pastel white dot near tip */}
                  <circle cx="198" cy="68" r="4.5" fill="#FFFFFF" />
                </g>
              </g>

              {/* Pinky: shortest, leaning right (~ +9°) */}
              <g transform="rotate(9 242 195)">
                <g
                  id="right-finger-3"
                  className="finger finger-3"
                  onMouseEnter={() => setHoveredFinger('right-3')}
                  onMouseLeave={() => setHoveredFinger(null)}
                >
                  <rect
                    x="226"
                    y="85"
                    width="32"
                    height="110"
                    rx="16"
                    fill="#7B3FF2"
                  />
                  {/* Pastel white dot near tip */}
                  <circle cx="242" cy="103" r="4.5" fill="#FFFFFF" />
                </g>
              </g>

              {/* 6. Foreground Tiles Overlapping the Wrist Base */}
              <g className="foreground-tiles">
                {renderForegroundTile('rt-1', 106, 333, 24, 8)}
                {renderForegroundTile('rt-2', 132, 327, 26, 16)}
                {renderForegroundTile('rt-3', 158, 331, 25, 11)}
                {renderForegroundTile('rt-4', 185, 326, 26, 18)}
                {renderForegroundTile('rt-5', 212, 334, 26, 8)}
                {renderForegroundTile('rt-6', 238, 330, 24, 14)}
              </g>
            </g>
          </svg>
        </div>
      </div>
    </div>
  );
};
