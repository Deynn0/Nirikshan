// GLSL shaders for WebGL Eye Scene (Sclera, Voxel Lids, Iris, and Lens)

export const scleraVertex = /* glsl */ `
varying vec2 vUv;
varying vec2 vPos;
uniform vec2 uHalf;

void main() {
  vUv = uv;
  vPos = position.xy * uHalf;
  gl_Position = vec4(position.xy, 0.999, 1.0);
}
`;

export const scleraFragment = /* glsl */ `
varying vec2 vUv;
varying vec2 vPos;

uniform vec4 uShape;
uniform float uOpen;
uniform vec2 uHalf;
uniform float uCamY;
uniform vec3 uPeach;
uniform vec3 uApricot;
uniform vec3 uRose;
uniform vec3 uLilac;
uniform vec3 uGlow;
uniform vec3 uShade;

void main() {
  // 180° vertical linear gradient: Peach (0%), Apricot (34%), Rose (70%), Lilac (100%)
  // ny = 1.0 at top, ny = 0.0 at bottom
  float ny = clamp((vPos.y / uHalf.y) * 0.5 + 0.5, 0.0, 1.0);
  vec3 sky;
  if (ny >= 0.66) {
    sky = mix(uApricot, uPeach, (ny - 0.66) / 0.34);
  } else if (ny >= 0.30) {
    sky = mix(uRose, uApricot, (ny - 0.30) / 0.36);
  } else {
    sky = mix(uLilac, uRose, ny / 0.30);
  }

  // Soft radial glow centered at 50% 52% (slightly below center)
  vec2 glowCenter = vec2(0.0, -uHalf.y * 0.04);
  float dCenter = length((vPos - glowCenter) / vec2(uHalf.x * 0.60, uHalf.y * 0.55));
  float glow = smoothstep(0.70, 0.0, dCenter) * 0.90;
  vec3 col = mix(sky, uGlow, glow);

  gl_FragColor = vec4(col, 1.0);
}
`;

export const lidVertex = /* glsl */ `
attribute vec2 aCell;
attribute float aSeed;

uniform vec4 uShape;
uniform float uOpen;
uniform float uTime;
uniform vec4 uPulse[4];
uniform float uCell;
uniform float uMaxH;
uniform float uRamp;
uniform vec3 uCursor;

varying vec3 vNormal;
varying float vIsRim;
varying float vSeed;
varying float vHeight;

void main() {
  vNormal = normal;
  vSeed = aSeed;

  float ax = abs(aCell.x);
  float d = -1.0;
  if (ax < uShape.x) {
    float u = ax / uShape.x;
    float f = pow(max(0.0, 1.0 - u * u), uShape.w);
    float topY = uShape.y * f * uOpen;
    float btmY = -uShape.z * f * uOpen;
    if (aCell.y > topY) {
      d = aCell.y - topY;
    } else if (aCell.y < btmY) {
      d = btmY - aCell.y;
    } else {
      d = -1.0;
    }
  } else {
    float dx = ax - uShape.x;
    d = length(vec2(dx, aCell.y));
  }

  float h = 0.0;
  float isRim = 0.0;

  if (d > 0.0) {
    h = min(uMaxH, (d / uRamp) * uMaxH);
    h += (aSeed - 0.5) * 0.12 * uMaxH;

    if (d < uCell * 1.5) {
      isRim = 1.0;
      h = max(h, uCell * 0.85);
    }

    // Cursor proximity wave
    float curDist = length(aCell - uCursor.xy);
    float wave = sin(curDist * 2.8 - uTime * 3.5) * exp(-curDist * 0.7) * 0.3 * uCursor.z;
    h = max(0.05, h + wave);

    // Pulse shockwaves
    for (int i = 0; i < 4; i++) {
      if (uPulse[i].w > 0.5) {
        float dt = uTime - uPulse[i].z;
        if (dt >= 0.0 && dt < 1.4) {
          float pr = dt * 6.5;
          float pDist = length(aCell - uPulse[i].xy);
          float ring = exp(-pow((pDist - pr) * 2.2, 2.0));
          h += ring * max(0.0, 1.0 - dt / 1.4) * 0.55;
        }
      }
    }
  } else {
    h = 0.001;
  }

  vIsRim = isRim;
  vHeight = h;

  vec3 pos = position;
  pos.xy *= uCell * 0.94;
  pos.z *= h;

  pos.x += aCell.x;
  pos.y += aCell.y;

  if (d <= 0.0) {
    pos.z -= 10.0;
  }

  gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
}
`;

export const lidFragment = /* glsl */ `
uniform vec3 uTop;
uniform vec3 uSide;
uniform vec3 uSideDeep;
uniform vec3 uRim;

varying vec3 vNormal;
varying float vIsRim;
varying float vSeed;
varying float vHeight;

void main() {
  vec3 col;
  if (vNormal.z > 0.75) {
    // Cube Top Face: #c8b6f5 (soft lavender)
    // Rim Reflection: #ffd9bf (peach highlight) on edge voxels
    col = vIsRim > 0.5 ? mix(uTop, uRim, 0.55) : uTop;
    col *= (0.95 + 0.10 * vSeed);
  } else if (vNormal.y < -0.35 || vNormal.x > 0.35) {
    // Cube Side Face: #8f6fd8 (mid purple)
    col = uSide * (0.95 + 0.10 * vSeed);
  } else {
    // Cube Deep Shadow: #5f43b3 (deep purple)
    col = uSideDeep * (0.95 + 0.10 * vSeed);
  }

  // Subtle peach rim reflection on edge side faces towards the opening
  if (vIsRim > 0.5 && vNormal.z < 0.75) {
    col = mix(col, uRim, 0.28);
  }

  gl_FragColor = vec4(col, 1.0);
}
`;

export const irisVertex = /* glsl */ `
attribute vec4 aPolar;
attribute vec2 aRnd;

uniform float uPupilR;
uniform float uIrisR;
uniform float uTime;

varying float vR;
varying float vTheta;
varying vec3 vNormal;
varying vec2 vRnd;

void main() {
  vNormal = normal;
  vRnd = aRnd;

  float r = aPolar.x + position.x * aPolar.z * 0.94;
  float th = aPolar.y + position.y * aPolar.w * 0.88;
  vR = r;
  vTheta = th;

  float h = 0.24 + 0.08 * aRnd.x;
  vec3 pos;
  pos.x = r * cos(th);
  pos.y = r * sin(th);
  pos.z = position.z * h;

  gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
}
`;

export const irisFragment = /* glsl */ `
uniform float uTime;
uniform vec4 uPulse[4];
uniform vec4 uRead[4];
uniform float uPupilR;
uniform float uIrisR;
uniform vec3 uInner;
uniform vec3 uMid;
uniform vec3 uOuter;
uniform vec3 uLimbal;
uniform vec3 uFadeTo;
uniform float uFade;
uniform vec3 uToneOk;
uniform vec3 uToneWarn;
uniform vec3 uToneBad;

varying float vR;
varying float vTheta;
varying vec3 vNormal;
varying vec2 vRnd;

void main() {
  float span = max(0.01, uIrisR - uPupilR);
  float t = clamp((vR - uPupilR) / span, 0.0, 1.0);

  // Gradient along radius:
  // Inner Iris: #7a36ee (vibrant purple)
  // Mid Iris: #b45ee0 (magenta-purple)
  // Outer Iris: #f3a3c7 (soft pink)
  // Limbal Outer Ring: #3b157f (deep violet)
  vec3 baseCol;
  if (t < 0.45) {
    baseCol = mix(uInner, uMid, t / 0.45);
  } else if (t < 0.82) {
    baseCol = mix(uMid, uOuter, (t - 0.45) / 0.37);
  } else {
    baseCol = mix(uOuter, uLimbal, (t - 0.82) / 0.18);
  }

  // Spoke fibrous variation
  baseCol *= (0.88 + 0.24 * vRnd.x);

  // Scanline highlights
  for (int i = 0; i < 4; i++) {
    if (uRead[i].w > 0.5) {
      float dt = uTime - uRead[i].y;
      if (dt >= 0.0 && dt < 1.2) {
        float dAngle = abs(mod(vTheta - uRead[i].x + 3.14159, 6.28318) - 3.14159);
        float scan = smoothstep(0.32, 0.0, dAngle) * max(0.0, 1.0 - dt / 1.2);
        vec3 toneCol = uRead[i].z > 0.5 ? uToneOk : (uRead[i].z < -0.5 ? uToneBad : uToneWarn);
        baseCol = mix(baseCol, toneCol, scan * 0.7);
      }
    }
  }

  if (vNormal.z < 0.5) {
    baseCol *= 0.78;
  }

  vec3 finalCol = mix(baseCol, uFadeTo, uFade);
  gl_FragColor = vec4(finalCol, 1.0);
}
`;

export const lensVertex = /* glsl */ `
varying vec2 vUv;

void main() {
  vUv = uv;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

export const lensFragment = /* glsl */ `
uniform vec3 uLens;
uniform vec3 uEdge;
uniform vec3 uRuff;
uniform float uScale;

varying vec2 vUv;

void main() {
  vec2 p = (vUv - 0.5) * 2.0;
  float r = length(p);
  if (r > 1.0) discard;

  // Center Lens (Disc): #fffaf6 (translucent warm white)
  // Subtle soft radial rim shading to give clean depth
  float edgeShade = smoothstep(0.82, 1.0, r) * 0.06;
  vec3 col = mix(uLens, vec3(0.94, 0.91, 0.96), edgeShade);

  // Soft specular glints
  float d1 = length(vUv - vec2(0.38, 0.62));
  float glint1 = smoothstep(0.12, 0.01, d1) * 0.35;

  float d2 = length(vUv - vec2(0.62, 0.38));
  float glint2 = smoothstep(0.08, 0.01, d2) * 0.20;

  col = mix(col, vec3(1.0), glint1 + glint2);

  // Solid warm white disc backdrop for typography readability
  gl_FragColor = vec4(col, 1.0);
}
`;
