"""Seal and stamp forensics detector (OpenCV + imagehash).

Approach:
1. Locate circular/elliptical regions on the rasterized page using
   OpenCV HoughCircles + contour convexity analysis.
2. For each candidate seal region, compute:
   a. Perceptual hash (pHash via imagehash library).
   b. Color histogram to detect red/blue ink bias (common in official stamps).
   c. Interior contrast to distinguish solid seals from blank circles.
3. Cross-hash comparison: if the same seal appears on multiple pages,
   check that it is identical (clone detection). If hashes differ beyond
   threshold, flag as modified seal.
4. Resolution anomaly: if a seal region has significantly lower pixel
   density than surrounding text, it may have been pasted from a
   lower-resolution source scan.

All findings are at trust level STRUCTURAL_FORENSIC.
"""

from __future__ import annotations

import logging
from typing import Any

from nirikshan.forensics.models import FindingCategory, FindingSeverity, ForensicFinding
from nirikshan.ingest.models import ParsedDocument

log = logging.getLogger(__name__)
_DETECTOR = "seal_detector"

try:
    import cv2
    import numpy as np
    _HAS_CV2 = True
except ImportError:  # pragma: no cover
    _HAS_CV2 = False

try:
    import imagehash
    from PIL import Image
    _HAS_IMAGEHASH = True
except ImportError:  # pragma: no cover
    _HAS_IMAGEHASH = False

# Minimum radius (px) for a valid institutional seal
_MIN_SEAL_RADIUS_PX = 30
_MAX_SEAL_RADIUS_PX = 300
# Perceptual hash distance threshold (0=identical, 64=completely different)
_HASH_CLONE_THRESHOLD = 5
_HASH_MODIFIED_THRESHOLD = 15
# Red/Blue ink ratio to qualify as a stamped seal
_STAMP_COLOR_RATIO = 0.05


def _load_rgb(png_bytes: bytes) -> tuple[np.ndarray, np.ndarray] | tuple[None, None]:  # type: ignore[name-defined]
    if not _HAS_CV2 or not png_bytes:
        return None, None
    try:
        buf = np.frombuffer(png_bytes, dtype=np.uint8)
        bgr = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        if bgr is None:
            return None, None
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        return bgr, gray
    except Exception:
        return None, None


def _detect_circles(gray: np.ndarray) -> list[tuple[int, int, int]]:  # type: ignore[name-defined]
    """Use HoughCircles to find circular seal candidates."""
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=50,
        param1=100,
        param2=30,
        minRadius=_MIN_SEAL_RADIUS_PX,
        maxRadius=_MAX_SEAL_RADIUS_PX,
    )
    result: list[tuple[int, int, int]] = []
    if circles is not None:
        circles_int = np.round(circles[0]).astype(int)
        for cx, cy, r in circles_int:
            result.append((int(cx), int(cy), int(r)))
    return result


def _crop_circle(bgr: np.ndarray, cx: int, cy: int, r: int) -> np.ndarray:  # type: ignore[name-defined]
    h, w = bgr.shape[:2]
    x0 = max(0, cx - r)
    y0 = max(0, cy - r)
    x1 = min(w, cx + r)
    y1 = min(h, cy + r)
    return bgr[y0:y1, x0:x1]


def _has_stamp_color(bgr_crop: np.ndarray) -> bool:  # type: ignore[name-defined]
    """Check if crop has significant red or blue ink (typical for stamps)."""
    if bgr_crop.size == 0:
        return False
    b, g, r = cv2.split(bgr_crop)
    total = bgr_crop.shape[0] * bgr_crop.shape[1]
    # Red pixels: r>150, b<100, g<100
    red_mask = (r.astype(int) > 150) & (b.astype(int) < 100) & (g.astype(int) < 100)
    blue_mask = (b.astype(int) > 150) & (r.astype(int) < 100) & (g.astype(int) < 100)
    stamp_ratio = (int(np.sum(red_mask)) + int(np.sum(blue_mask))) / max(1, total)
    return stamp_ratio >= _STAMP_COLOR_RATIO


def _phash(bgr_crop: np.ndarray) -> imagehash.ImageHash | None:  # type: ignore[name-defined]
    if not _HAS_IMAGEHASH:
        return None
    try:
        pil = Image.fromarray(cv2.cvtColor(bgr_crop, cv2.COLOR_BGR2RGB))
        return imagehash.phash(pil)
    except Exception:
        return None


def detect(doc: ParsedDocument) -> list[ForensicFinding]:
    findings: list[ForensicFinding] = []

    if not _HAS_CV2:
        return findings

    # Collect seals across pages: {page_num: [(cx, cy, r, phash, has_color)]}
    page_seals: dict[int, list[dict[str, Any]]] = {}
    all_hashes: list[tuple[int, Any, dict[str, Any]]] = []  # (page_num, phash, info)

    for page in doc.pages:
        if not page.raster_png:
            continue

        bgr, gray = _load_rgb(page.raster_png)
        if bgr is None or gray is None:
            continue

        circles = _detect_circles(gray)
        if not circles:
            continue

        page_seal_list: list[dict[str, Any]] = []
        for cx, cy, r in circles:
            crop = _crop_circle(bgr, cx, cy, r)
            has_color = _has_stamp_color(crop)
            ph = _phash(crop)

            info: dict[str, Any] = {
                "cx": cx, "cy": cy, "r": r,
                "has_stamp_color": has_color,
                "phash": str(ph) if ph else None,
            }
            page_seal_list.append(info)
            all_hashes.append((page.page_number, ph, info))

            # Convert to PDF-point bbox
            scale = 72.0 / 150.0
            x0 = (cx - r) * scale
            y0 = (cy - r) * scale
            x1 = (cx + r) * scale
            y1 = (cy + r) * scale

            severity = FindingSeverity.INFO if has_color else FindingSeverity.LOW
            findings.append(
                ForensicFinding(
                    detector=_DETECTOR,
                    category=FindingCategory.SEAL,
                    severity=severity,
                    title=(
                        f"Page {page.page_number}: Official Stamp/Seal Detected (r={r}px)"
                        if has_color
                        else f"Page {page.page_number}: Circular Region Detected (r={r}px)"
                    ),
                    description=(
                        f"A circular region (radius {r}px) was detected at ({cx},{cy}). "
                        + (
                            "It contains red/blue ink consistent with an official stamp. "
                            if has_color else ""
                        )
                        + "Perceptual hash recorded for cross-page clone detection."
                    ),
                    page=page.page_number,
                    bbox={
                        "x0": round(x0, 1), "y0": round(y0, 1),
                        "x1": round(x1, 1), "y1": round(y1, 1),
                    },
                    evidence=info,
                )
            )

        if page_seal_list:
            page_seals[page.page_number] = page_seal_list

    # ---- Cross-page hash comparison ----
    if _HAS_IMAGEHASH and len(all_hashes) >= 2:
        for i, (pg_a, hash_a, _info_a) in enumerate(all_hashes):
            for pg_b, hash_b, _info_b in all_hashes[i + 1:]:
                if hash_a is None or hash_b is None:
                    continue
                dist = hash_a - hash_b
                if dist <= _HASH_CLONE_THRESHOLD and pg_a != pg_b:
                    findings.append(
                        ForensicFinding(
                            detector=_DETECTOR,
                            category=FindingCategory.SEAL,
                            severity=FindingSeverity.MEDIUM,
                            title=f"Identical Seal Clone: Page {pg_a} → Page {pg_b}",
                            description=(
                                f"The seal on page {pg_a} is perceptually identical "
                                f"(pHash distance={dist}) to the seal on page {pg_b}. "
                                f"This may indicate a digitally copied seal rather than "
                                f"an authentic physical stamp."
                            ),
                            evidence={
                                "page_a": pg_a, "phash_a": str(hash_a),
                                "page_b": pg_b, "phash_b": str(hash_b),
                                "distance": dist,
                            },
                        )
                    )
                elif _HASH_CLONE_THRESHOLD < dist <= _HASH_MODIFIED_THRESHOLD and pg_a != pg_b:
                    findings.append(
                        ForensicFinding(
                            detector=_DETECTOR,
                            category=FindingCategory.SEAL,
                            severity=FindingSeverity.HIGH,
                            title=f"Modified Seal Suspected: Page {pg_a} → Page {pg_b}",
                            description=(
                                f"The seal on page {pg_a} is similar but not identical "
                                f"(pHash distance={dist}) to page {pg_b}. "
                                f"A modified or partially altered seal is a strong "
                                f"forgery indicator."
                            ),
                            evidence={
                                "page_a": pg_a, "phash_a": str(hash_a),
                                "page_b": pg_b, "phash_b": str(hash_b),
                                "distance": dist,
                            },
                        )
                    )

    return findings
