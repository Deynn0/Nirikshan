// Hand geometry carried over from the v2 OK-sign hands, redrawn with Canvas2D so it can feed WebGL textures
import { palette } from "../../landing/palette";

export type Hue = "rose" | "violet";

// Hand-local units: a right hand seen palm first, thumb and index forming a ring on the left
export const RING = { x: 112, y: 222 };
export const PALM_EYE = { x: 243, y: 326 };
export const PIVOT = { x: 243, y: 456 };
// Hand-local y that sits on the block tops when a hand is fully up; the wrist and cuff stay below it
export const CUT = 392;
// The cuff starts well below the cut, so lifting a hand to hold the certificate shows wrist, not sleeve
export const CUFF_TOP = 540;

// Two poses share one command layout (M, C, C) so they interpolate number by number
const INDEX = {
  ok: [178, 262, 178, 185.5, 148.5, 156, 112, 156, 75.5, 156, 46, 185.5, 46, 222],
  open: [178, 262, 177.5, 226, 177, 200, 176.5, 176, 176, 150, 175, 120, 174, 92],
};
const THUMB = {
  ok: [172, 348, 162, 318, 148.5, 288, 112, 288, 75.5, 288, 46, 258.5, 46, 222],
  open: [172, 348, 154, 336, 136, 322, 118, 306, 100, 290, 84, 272, 70, 250],
};
const NAIL = { ok: [46, 222], open: [174, 104] };

export const HUES: Record<Hue, { base: string; shade: string; tips: [string, string, string]; nail: string }> = {
  violet: { base: palette.brand[500], shade: palette.brand[600], tips: [palette.brand[200], palette.peach, "#ffffff"], nail: "#ffffff" },
  rose: { base: "#e88fb8", shade: "#d4729f", tips: [palette.lilac, palette.peach, "#ffffff"], nail: "#ffffff" },
};
export const CUFF = { body: "#ffffff", band: palette.brand[100], dots: palette.brand[400] };
export const EYE_INK = palette.ink;

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

function bezier(nums: number[]): Path2D {
  const n = nums.map((v) => v.toFixed(2));
  return new Path2D(`M ${n[0]} ${n[1]} C ${n[2]} ${n[3]} ${n[4]} ${n[5]} ${n[6]} ${n[7]} C ${n[8]} ${n[9]} ${n[10]} ${n[11]} ${n[12]} ${n[13]}`);
}

function mixNums(a: number[], b: number[], t: number) {
  return a.map((v, i) => lerp(v, b[i], t));
}

function stroke(ctx: CanvasRenderingContext2D, p: Path2D, color: string, width: number) {
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.stroke(p);
}

function dot(ctx: CanvasRenderingContext2D, x: number, y: number, r: number, color: string) {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.fill();
}

function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number, color: string) {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, r);
  ctx.fill();
}

// The free fingers (middle, ring, little); thumb and index stay closed around the eye
export const FREE_FINGERS = [
  { b: [222, 262], t: [220, 72], w: 42, dot: 12, r: 10 },
  { b: [267, 264], t: [271, 90], w: 42, dot: 12, r: 10 },
  { b: [309, 272], t: [319, 142], w: 39, dot: 11, r: 9.5 },
] as const;
export type Folds = [number, number, number];

// Tip of a free finger folded by f: the finger shortens toward the palm as it curls
export function fingerTip(j: number, f: number): [number, number] {
  const F = FREE_FINGERS[j];
  const k = 1 - 0.46 * Math.max(-0.15, Math.min(1.1, f));
  return [F.b[0] + (F.t[0] - F.b[0]) * k, F.b[1] + (F.t[1] - F.b[1]) * k];
}

// Texture windows in hand units
export const UPPER_BOX = { x0: -24, y0: 18, x1: 384, y1: 452 };
export const CUFF_BOX = { x0: 150, y0: 380, x1: 336, y1: 820 };

// Fingers, thumb and palm: everything that leans about the wrist pivot
export function drawUpper(ctx: CanvasRenderingContext2D, hue: Hue, pose: number, tapDeg: number, folds: Folds = [0, 0, 0]) {
  const c = HUES[hue];
  ctx.lineCap = "round";

  // 1. Index finger (curving smoothly to form top of OK ring in shade color)
  ctx.save();
  ctx.translate(178, 244);
  ctx.rotate((tapDeg * Math.PI) / 180);
  ctx.translate(-178, -244);
  stroke(ctx, bezier(mixNums(INDEX.ok, INDEX.open, pose)), c.shade, 42);
  ctx.restore();

  const line = (x0: number, y0: number, x1: number, y1: number, w: number) => {
    const p = new Path2D();
    p.moveTo(x0, y0);
    p.lineTo(x1, y1);
    stroke(ctx, p, c.base, w);
  };

  // 2. Free fingers (middle, ring, pinky)
  FREE_FINGERS.forEach((F, j) => {
    const f = folds[j];
    const [tx, ty] = fingerTip(j, f);
    line(F.b[0], F.b[1], tx, ty, F.w);
    const len = Math.hypot(F.t[0] - F.b[0], F.t[1] - F.b[1]);
    const ux = (F.t[0] - F.b[0]) / len;
    const uy = (F.t[1] - F.b[1]) / len;
    // curled top knuckle tone
    if (f > 0.02) {
      const p = new Path2D();
      p.moveTo(tx - ux * len * 0.2 * f, ty - uy * len * 0.2 * f);
      p.lineTo(tx, ty);
      ctx.globalAlpha = Math.min(1, f * 1.4);
      stroke(ctx, p, c.shade, F.w * 0.94);
      ctx.globalAlpha = 1;
    }
    dot(ctx, tx - ux * F.dot, ty - uy * F.dot, F.r * (1 - 0.25 * Math.max(0, f)), c.tips[j]);
  });

  // 3. Thumb (curving smoothly to meet index finger at the pinch apex)
  stroke(ctx, bezier(mixNums(THUMB.ok, THUMB.open, pose)), c.base, 42);

  // 4. Smooth Palm Contour: organic silhouette flowing into wrist and finger roots
  const palm = new Path2D();
  palm.moveTo(328, 272);
  palm.bezierCurveTo(336, 310, 332, 360, 306, 392);
  palm.lineTo(180, 392);
  palm.bezierCurveTo(170, 365, 168, 340, 172, 320);
  palm.bezierCurveTo(172, 320, 175, 290, 184, 255);
  palm.bezierCurveTo(184, 255, 210, 252, 260, 254);
  palm.bezierCurveTo(260, 254, 300, 260, 328, 272);
  palm.closePath();
  ctx.fillStyle = c.base;
  ctx.fill(palm);

  // Knuckle root blends
  dot(ctx, 222, 262, 21, c.base);
  dot(ctx, 267, 264, 21, c.base);
  dot(ctx, 309, 272, 19.5, c.base);

  // In OK pose, guarantee pure circular opening of radius 45 around RING (112, 222)
  if (pose < 0.25) {
    ctx.save();
    ctx.globalCompositeOperation = "destination-out";
    ctx.beginPath();
    ctx.arc(RING.x, RING.y, 45 * (1 - pose * 4), 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  // White nail accent on index pinch tip
  dot(ctx, lerp(NAIL.ok[0], NAIL.open[0], pose), lerp(NAIL.ok[1], NAIL.open[1], pose), 9.5, c.nail);
}

// Wrist and cuff: they never lean, they stay rooted below the block tops
export function drawCuff(ctx: CanvasRenderingContext2D, hue: Hue, bottom = CUFF_BOX.y1) {
  const c = HUES[hue];
  ctx.fillStyle = c.base;
  ctx.fillRect(180, 390, 126, CUFF_TOP - 390 + 40);
  roundRect(ctx, 158, CUFF_TOP, 170, bottom - CUFF_TOP + 40, 30, CUFF.body);
  ctx.save();
  ctx.beginPath();
  ctx.rect(158, CUFF_TOP + 30, 170, bottom - CUFF_TOP + 10);
  ctx.clip();
  ctx.fillStyle = CUFF.dots;
  for (let y = CUFF_TOP + 26; y < bottom + 34; y += 34) {
    for (let x = 136; x < 340; x += 34) {
      ctx.beginPath();
      ctx.moveTo(x + 13, y + 10);
      ctx.arc(x + 8, y + 10, 5, 0, Math.PI * 2);
      ctx.moveTo(x + 30, y + 27);
      ctx.arc(x + 25, y + 27, 5, 0, Math.PI * 2);
      ctx.fill();
    }
  }
  ctx.restore();
  roundRect(ctx, 158, CUFF_TOP, 170, 30, 15, CUFF.band);
}

// Almond eye drawn around (0,0) in hand units; the WebGL path draws the same shape in a shader
export function drawEye(ctx: CanvasRenderingContext2D, px = 0, py = 0, open = 1) {
  ctx.save();
  ctx.scale(1, Math.max(0.05, open));
  const almond = new Path2D("M -40 0 C -24 -32 24 -32 40 0 C 24 32 -24 32 -40 0 Z");
  ctx.fillStyle = "#ffffff";
  ctx.fill(almond);
  ctx.clip(almond);
  ctx.scale(1, 1 / Math.max(0.05, open));

  // Rounded square (squircle) pupil matching Pramana brand identity
  const s = 28;
  const r = 8;
  roundRect(ctx, px - s / 2, py - s / 2, s, s, r, EYE_INK);

  // Curious catchlight reflection inside pupil
  dot(ctx, px - 4.8, py - 5.5, 4.4, "#ffffff");
  ctx.restore();
}

export type HandPose = {
  hue: Hue;
  mirror: boolean;
  pose: number; // 0 OK sign, 1 open "wait" palm
  tapDeg?: number;
  folds?: Folds;
  tilt?: number; // degrees, screen space, about the wrist pivot
  eye?: { px: number; py: number; open: number };
};

// Whole hand for 2D canvases (static story and the no-WebGL fallback), clipped at a hand-local y
export function drawWholeHand(ctx: CanvasRenderingContext2D, h: HandPose, clipY = CUT) {
  ctx.save();
  ctx.beginPath();
  ctx.rect(-200, -200, 760, clipY + 200);
  ctx.clip();
  ctx.lineCap = "round";
  if (h.mirror) {
    ctx.translate(360, 0);
    ctx.scale(-1, 1);
  }
  drawCuff(ctx, h.hue, Math.max(clipY + 40, CUFF_TOP + 80));
  ctx.restore();
  ctx.save();
  ctx.beginPath();
  ctx.rect(-200, -200, 760, clipY + 200);
  ctx.clip();
  const pvx = h.mirror ? 360 - PIVOT.x : PIVOT.x;
  ctx.translate(pvx, PIVOT.y);
  ctx.rotate(((h.tilt ?? 0) * Math.PI) / 180);
  ctx.translate(-pvx, -PIVOT.y);
  ctx.save();
  if (h.mirror) {
    ctx.translate(360, 0);
    ctx.scale(-1, 1);
  }
  drawUpper(ctx, h.hue, h.pose, h.tapDeg ?? 0, h.folds);
  ctx.restore();
  const ex = lerp(RING.x, PALM_EYE.x, h.pose);
  const ey = lerp(RING.y, PALM_EYE.y, h.pose);
  ctx.translate(h.mirror ? 360 - ex : ex, ey);
  const sc = lerp(1, 1.08, h.pose);
  ctx.scale(sc, sc);
  drawEye(ctx, h.eye?.px ?? 0, h.eye?.py ?? 0, h.eye?.open ?? 1);
  ctx.restore();
}

// Tap: the index lifts off the thumb and presses back twice, the ring confirms
export function tapAngle(elapsedMs: number): number {
  const u = elapsedMs / 760;
  if (u <= 0 || u >= 1) return 0;
  const keys: [number, number][] = [
    [0, 0],
    [0.22, 11],
    [0.42, -2],
    [0.62, 8],
    [1, 0],
  ];
  for (let i = 1; i < keys.length; i++) {
    if (u <= keys[i][0]) {
      const [t0, a0] = keys[i - 1];
      const [t1, a1] = keys[i];
      const k = (u - t0) / (t1 - t0);
      const e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
      return lerp(a0, a1, e);
    }
  }
  return 0;
}

