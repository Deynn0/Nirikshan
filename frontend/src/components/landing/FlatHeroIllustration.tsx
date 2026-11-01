import React, { useEffect, useState } from 'react';

export const FlatHeroIllustration: React.FC = () => {
  const [mouseOffset, setMouseOffset] = useState({ x: -4, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      // Calculate normalized mouse offset between -1 and 1
      const nx = (e.clientX / window.innerWidth) * 2 - 1;
      const ny = (e.clientY / window.innerHeight) * 2 - 1;
      // Pupil looks primarily left (baseline -4px), with ±4px mouse parallax
      setMouseOffset({
        x: -5 + nx * 3.5,
        y: ny * 3,
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className="relative w-full h-full flex items-end justify-center pointer-events-none select-none">
      {/* 1. Full-Width Perspective Tiled Floor (Lavender low-poly terrain) */}
      <div className="absolute inset-x-0 bottom-0 h-[42%] w-full overflow-hidden">
        <svg
          className="w-full h-full block"
          viewBox="0 0 1400 400"
          preserveAspectRatio="none"
        >
          <defs>
            {/* Misty haze fade at the horizon */}
            <linearGradient id="horizonHaze" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#EAE2FB" stopOpacity="1" />
              <stop offset="25%" stopColor="#EAE2FB" stopOpacity="0.85" />
              <stop offset="70%" stopColor="#EAE2FB" stopOpacity="0.15" />
              <stop offset="100%" stopColor="#EAE2FB" stopOpacity="0" />
            </linearGradient>

            {/* Darker gap floor base */}
            <linearGradient id="floorBase" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#A896E6" />
              <stop offset="100%" stopColor="#7E6ABF" />
            </linearGradient>
          </defs>

          {/* Dark gap background base */}
          <rect x="0" y="0" width="1400" height="400" fill="url(#floorBase)" />

          {/* Perspective Tile Grid Rows */}
          {/* Row 0 (near horizon, small compressed tiles) */}
          <g opacity="0.7">
            {Array.from({ length: 28 }).map((_, i) => {
              const x1 = (i / 28) * 1400;
              const x2 = ((i + 1) / 28) * 1400;
              const x1b = ((i - 1) / 26) * 1400;
              const x2b = (i / 26) * 1400;
              const fill = i % 2 === 0 ? '#B9A8F0' : '#B29FEA';
              return (
                <polygon
                  key={`r0-${i}`}
                  points={`${x1 + 1},10 ${x2 - 1},10 ${x2b - 1},40 ${x1b + 1},40`}
                  fill={fill}
                />
              );
            })}
          </g>

          {/* Row 1 */}
          <g opacity="0.85">
            {Array.from({ length: 24 }).map((_, i) => {
              const x1 = (i / 24) * 1400;
              const x2 = ((i + 1) / 24) * 1400;
              const x1b = ((i - 0.5) / 23) * 1400;
              const x2b = ((i + 0.5) / 23) * 1400;
              const fill = i % 3 === 0 ? '#B5A3EE' : i % 3 === 1 ? '#AE9CE7' : '#B8A6F0';
              return (
                <polygon
                  key={`r1-${i}`}
                  points={`${x1 + 1.5},42 ${x2 - 1.5},42 ${x2b - 1.5},85 ${x1b + 1.5},85`}
                  fill={fill}
                />
              );
            })}
          </g>

          {/* Row 2 with some slightly raised tiles */}
          <g>
            {Array.from({ length: 20 }).map((_, i) => {
              const x1 = (i / 20) * 1400;
              const x2 = ((i + 1) / 20) * 1400;
              const x1b = ((i - 0.5) / 19) * 1400;
              const x2b = ((i + 0.5) / 19) * 1400;
              const isRaised = i === 6 || i === 12 || i === 15;
              const fill = isRaised ? '#C4B5F7' : i % 2 === 0 ? '#AA97E5' : '#A38FE0';
              return (
                <g key={`r2-${i}`}>
                  {isRaised && (
                    <polygon
                      points={`${x1b + 2},140 ${x2b - 2},140 ${x2b - 2},148 ${x1b + 2},148`}
                      fill="#816DBF"
                    />
                  )}
                  <polygon
                    points={`${x1 + 2},88 ${x2 - 2},88 ${x2b - 2},${isRaised ? 134 : 140} ${x1b + 2},${isRaised ? 134 : 140}`}
                    fill={fill}
                  />
                </g>
              );
            })}
          </g>

          {/* Row 3 (Mid perspective with raised blocks around center hands) */}
          <g>
            {Array.from({ length: 16 }).map((_, i) => {
              const x1 = (i / 16) * 1400;
              const x2 = ((i + 1) / 16) * 1400;
              const x1b = ((i - 0.5) / 15) * 1400;
              const x2b = ((i + 0.5) / 15) * 1400;
              // Tiles around center (i=7, 8, 9, 10) have small height variation
              const isRaised = i === 8 || i === 9 || i === 4;
              const fill = isRaised ? '#C0B0F5' : i % 2 === 0 ? '#A18DDD' : '#9B87E8';
              return (
                <g key={`r3-${i}`}>
                  {isRaised && (
                    <polygon
                      points={`${x1b + 2.5},210 ${x2b - 2.5},210 ${x2b - 2.5},222 ${x1b + 2.5},222`}
                      fill="#7964CC"
                    />
                  )}
                  <polygon
                    points={`${x1 + 2.5},143 ${x2 - 2.5},143 ${x2b - 2.5},${isRaised ? 202 : 210} ${x1b + 2.5},${isRaised ? 202 : 210}`}
                    fill={fill}
                  />
                </g>
              );
            })}
          </g>

          {/* Row 4 (Foreground large tiles with low-poly raised terrain) */}
          <g>
            {Array.from({ length: 12 }).map((_, i) => {
              const x1 = (i / 12) * 1400;
              const x2 = ((i + 1) / 12) * 1400;
              const x1b = ((i - 0.5) / 11) * 1400;
              const x2b = ((i + 0.5) / 11) * 1400;
              const isRaised = i === 6 || i === 7 || i === 2;
              const fill = isRaised ? '#BAA9F2' : i % 2 === 0 ? '#9883E3' : '#8E79DB';
              return (
                <g key={`r4-${i}`}>
                  {isRaised && (
                    <polygon
                      points={`${x1b + 3},295 ${x2b - 3},295 ${x2b - 3},312 ${x1b + 3},312`}
                      fill="#6D58BC"
                    />
                  )}
                  <polygon
                    points={`${x1 + 3},214 ${x2 - 3},214 ${x2b - 3},${isRaised ? 284 : 295} ${x1b + 3},${isRaised ? 284 : 295}`}
                    fill={fill}
                  />
                </g>
              );
            })}
          </g>

          {/* Row 5 (Immediate foreground, largest tiles) */}
          <g>
            {Array.from({ length: 9 }).map((_, i) => {
              const x1 = (i / 9) * 1400;
              const x2 = ((i + 1) / 9) * 1400;
              const x1b = ((i - 0.5) / 8) * 1400;
              const x2b = ((i + 0.5) / 8) * 1400;
              const fill = i % 2 === 0 ? '#917CD6' : '#8771CE';
              return (
                <polygon
                  key={`r5-${i}`}
                  points={`${x1 + 3.5},300 ${x2 - 3.5},300 ${x2b - 3.5},400 ${x1b + 3.5},400`}
                  fill={fill}
                />
              );
            })}
          </g>

          {/* Misty horizon haze overlay (top 35% of floor) */}
          <rect x="0" y="0" width="1400" height="140" fill="url(#horizonHaze)" />
        </svg>
      </div>

      {/* 2. Flat 2D Vector Hands (Side by Side, Upright, Not Overlapping, Rising from Floor) */}
      <div className="relative z-20 flex items-end justify-center gap-12 sm:gap-16 lg:gap-20 mb-[-24px]">
        {/* Left Hand: Dusty Pink (#E07A9B) */}
        <div className="relative flex flex-col items-center animate-bounce-subtle">
          <svg
            width="170"
            height="360"
            viewBox="0 0 170 360"
            fill="none"
            className="overflow-visible filter drop-shadow-[0_8px_16px_rgba(224,122,155,0.22)]"
          >
            {/* Wrist & Forearm */}
            <rect x="52" y="190" width="66" height="170" rx="33" fill="#E07A9B" />

            {/* Three Straight Upright Fingers */}
            {/* Middle Finger (tallest) */}
            <rect x="56" y="22" width="26" height="150" rx="13" fill="#E07A9B" />
            {/* Ring Finger */}
            <rect x="88" y="44" width="25" height="130" rx="12.5" fill="#E07A9B" />
            {/* Pinky Finger */}
            <rect x="119" y="74" width="24" height="100" rx="12" fill="#E07A9B" />

            {/* Fingertip Dots in contrasting pale yellow / soft cream */}
            <circle cx="69" cy="35" r="5.5" fill="#FEF08A" />
            <circle cx="100.5" cy="57" r="5.5" fill="#FEF08A" />
            <circle cx="131" cy="86" r="5.5" fill="#FEF08A" />

            {/* Palm & Thumb/Index "OK" Ring */}
            {/* Main Outer O-loop */}
            <path
              d="M 58 128 C 30 128 12 148 12 182 C 12 216 32 238 65 238 C 96 238 116 218 116 182 C 116 150 98 128 58 128 Z"
              fill="#E07A9B"
            />

            {/* Thumb knuckle dot */}
            <circle cx="24" cy="182" r="5.5" fill="#FEF08A" />

            {/* Inner Ring Cutout & Cartoon Eye Container */}
            {/* Eye Sclera (White Oval inside the ring) */}
            <ellipse cx="64" cy="183" rx="27" ry="29" fill="#FFFFFF" />

            {/* Black Pupil (looking left toward the text with mouse parallax) */}
            <ellipse
              cx={64 + mouseOffset.x}
              cy={183 + mouseOffset.y}
              rx="10.5"
              ry="12"
              fill="#18181B"
            />
            {/* Pupil Glint */}
            <circle
              cx={61 + mouseOffset.x}
              cy={180 + mouseOffset.y}
              r="3"
              fill="#FFFFFF"
            />
          </svg>
        </div>

        {/* Right Hand: Vivid Violet (#8B3DFF) */}
        <div className="relative flex flex-col items-center animate-bounce-delayed">
          <svg
            width="170"
            height="360"
            viewBox="0 0 170 360"
            fill="none"
            className="overflow-visible filter drop-shadow-[0_8px_16px_rgba(139,61,255,0.22)]"
          >
            {/* Wrist & Forearm */}
            <rect x="52" y="190" width="66" height="170" rx="33" fill="#8B3DFF" />

            {/* Three Straight Upright Fingers */}
            {/* Middle Finger (tallest) */}
            <rect x="56" y="22" width="26" height="150" rx="13" fill="#8B3DFF" />
            {/* Ring Finger */}
            <rect x="88" y="44" width="25" height="130" rx="12.5" fill="#8B3DFF" />
            {/* Pinky Finger */}
            <rect x="119" y="74" width="24" height="100" rx="12" fill="#8B3DFF" />

            {/* Fingertip Dots in contrasting pale yellow / soft lavender */}
            <circle cx="69" cy="35" r="5.5" fill="#FEF08A" />
            <circle cx="100.5" cy="57" r="5.5" fill="#FEF08A" />
            <circle cx="131" cy="86" r="5.5" fill="#FEF08A" />

            {/* Palm & Thumb/Index "OK" Ring */}
            <path
              d="M 58 128 C 30 128 12 148 12 182 C 12 216 32 238 65 238 C 96 238 116 218 116 182 C 116 150 98 128 58 128 Z"
              fill="#8B3DFF"
            />

            {/* Thumb knuckle dot */}
            <circle cx="24" cy="182" r="5.5" fill="#FEF08A" />

            {/* Eye Sclera (White Oval inside the ring) */}
            <ellipse cx="64" cy="183" rx="27" ry="29" fill="#FFFFFF" />

            {/* Black Pupil (looking left toward the text with mouse parallax) */}
            <ellipse
              cx={64 + mouseOffset.x}
              cy={183 + mouseOffset.y}
              rx="10.5"
              ry="12"
              fill="#18181B"
            />
            {/* Pupil Glint */}
            <circle
              cx={61 + mouseOffset.x}
              cy={180 + mouseOffset.y}
              r="3"
              fill="#FFFFFF"
            />
          </svg>
        </div>
      </div>

      {/* 3. Raised Grounding Tiles Covering Wrist Bases */}
      <div className="absolute inset-x-0 bottom-0 h-10 pointer-events-none flex justify-center items-end z-30">
        <div className="w-full max-w-lg flex justify-around px-8">
          <div className="w-24 h-5 bg-[#C0B0F5] rounded-t-sm shadow-xs border-t border-[#D6CAFA]" />
          <div className="w-24 h-6 bg-[#BAA9F2] rounded-t-sm shadow-xs border-t border-[#D6CAFA]" />
        </div>
      </div>
    </div>
  );
};
