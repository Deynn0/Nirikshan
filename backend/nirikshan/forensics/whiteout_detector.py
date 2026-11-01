"""Whiteout / white-rectangle overlay detector (OpenCV).

Approach:
1. Load the rasterized page PNG into OpenCV.
2. Detect large white or near-white rectangles (>50×10px) using:
   a. Simple threshold + contour analysis.
   b. Morphological close + rectangle detection.
3. Correlate with word-token positions: if a white rectangle overlaps
   a word bbox, it is a strong whiteout signal.
4. Also detect white-on-white text (invisible text) via color cluster
   analysis in a narrow strip around word bounding boxes.

All findings are at trust level STRUCTURAL_FORENSIC.
"""

from __future__ import annotations

import logging
from typing import Any

from nirikshan.forensics.models import FindingCategory, FindingSeverity, ForensicFinding
from nirikshan.ingest.models import ParsedDocument

log = logging.getLogger(__name__)
_DETECTOR = "whiteout_detector"

try:
    import cv2
    import numpy as np
    _HAS_CV2 = True
except ImportError:  # pragma: no cover
    _HAS_CV2 = False


# Minimum area in pixels for a rectangle to be considered a whiteout candidate
_MIN_AREA_PX = 500
# White / near-white threshold (0=black, 255=white)
_WHITE_THRESHOLD = 240
# Minimum fill ratio inside the rectangle to flag as solid white
_MIN_WHITE_FILL_RATIO = 0.90


def _load_gray(png_bytes: bytes) -> np.ndarray | None:  # type: ignore[name-defined]
    if not _HAS_CV2 or not png_bytes:
        return None
    try:
        buf = np.frombuffer(png_bytes, dtype=np.uint8)
        img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        if img is None:
            return None
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    except Exception as exc:
        log.debug("cv2 load failed: %s", exc)
        return None


def _find_white_rects(gray: np.ndarray) -> list[dict[str, Any]]:  # type: ignore[name-defined]
    """Find large white-filled rectangles in a grayscale image."""
    _, binary = cv2.threshold(gray, _WHITE_THRESHOLD, 255, cv2.THRESH_BINARY)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    h_img, w_img = gray.shape
    total_area = h_img * w_img

    rects: list[dict[str, Any]] = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < _MIN_AREA_PX or area >= total_area * 0.5:
            # Skip noise or whole-page background / bordered page area
            continue

        x, y, w, h = cv2.boundingRect(cnt)
        if w < 20 or h < 5 or (w > w_img * 0.75 and h > h_img * 0.75):
            continue

        # Check that the region is actually near-white
        region = gray[y: y + h, x: x + w]
        white_pixels = int(np.sum(region >= _WHITE_THRESHOLD))
        fill_ratio = white_pixels / max(1, region.size)

        if fill_ratio >= _MIN_WHITE_FILL_RATIO:
            rects.append({
                "x": int(x), "y": int(y),
                "w": int(w), "h": int(h),
                "area_px": int(area),
                "fill_ratio": round(fill_ratio, 3),
            })

    return rects


def _px_to_pts(px: float, page_h_pts: float, img_h_px: int, scale: float = 1.0) -> float:
    """Convert pixel y-coordinate to PDF points (flip y-axis)."""
    return page_h_pts - (px / scale * 72.0 / 150.0)


def detect(doc: ParsedDocument) -> list[ForensicFinding]:
    findings: list[ForensicFinding] = []

    if not _HAS_CV2:
        findings.append(
            ForensicFinding(
                detector=_DETECTOR,
                category=FindingCategory.WHITEOUT,
                severity=FindingSeverity.INFO,
                title="Whiteout Detector Skipped (opencv not installed)",
                description="Install opencv-python-headless to enable whiteout detection.",
            )
        )
        return findings

    scale = 150.0 / 72.0  # pixels per PDF point at 150 DPI

    for page in doc.pages:
        if not page.raster_png:
            continue

        gray = _load_gray(page.raster_png)
        if gray is None:
            continue

        h_img, w_img = gray.shape

        # 1. Check for text-layer tokens visually erased/covered by pure white
        concealed_words: list[str] = []
        concealed_bboxes: list[dict[str, float]] = []
        for word in page.words:
            # Skip single-character artifacts or whitespace
            if len(word.text.strip()) < 2:
                continue
            y0_px = max(0, int(word.bbox.y0 * scale))
            y1_px = min(h_img, int(word.bbox.y1 * scale))
            x0_px = max(0, int(word.bbox.x0 * scale))
            x1_px = min(w_img, int(word.bbox.x1 * scale))
            crop = gray[y0_px:y1_px, x0_px:x1_px]
            if crop.size >= 30 and float(np.min(crop)) >= 240.0:
                concealed_words.append(word.text)
                concealed_bboxes.append({
                    "x0": word.bbox.x0, "y0": word.bbox.y0,
                    "x1": word.bbox.x1, "y1": word.bbox.y1,
                })

        if concealed_words:
            first_bb = concealed_bboxes[0]
            findings.append(
                ForensicFinding(
                    detector=_DETECTOR,
                    category=FindingCategory.WHITEOUT,
                    severity=FindingSeverity.HIGH,
                    title=f"Page {page.page_number}: Whiteout Concealed Text Detected ({len(concealed_words)} word(s))",
                    description=(
                        f"Page {page.page_number} contains text in the PDF stream that is visually obscured "
                        f"by a white overlay: {concealed_words[:8]}. "
                        "White rectangles or invisible text are used to conceal dates and clauses in forged documents."
                    ),
                    page=page.page_number,
                    bbox=first_bb,
                    evidence={
                        "concealed_words": concealed_words[:15],
                        "total_concealed": len(concealed_words),
                    },
                )
            )

        # 2. Geometric white rectangle contour analysis
        white_rects = _find_white_rects(gray)

        for rect in white_rects:
            x_pts = rect["x"] / scale
            y_pts = rect["y"] / scale
            w_pts = rect["w"] / scale
            h_pts = rect["h"] / scale

            # Check overlap with any word token
            overlapping_words = []
            for word in page.words:
                bb = word.bbox
                if (bb.x0 < x_pts + w_pts and bb.x1 > x_pts and
                        bb.y0 < y_pts + h_pts and bb.y1 > y_pts):
                    overlapping_words.append(word.text)

            severity = FindingSeverity.HIGH if overlapping_words else FindingSeverity.MEDIUM
            title = (
                f"Page {page.page_number}: White Rectangle Overlaps Text ({len(overlapping_words)} word(s))"
                if overlapping_words
                else f"Page {page.page_number}: Large White Rectangle Detected"
            )

            findings.append(
                ForensicFinding(
                    detector=_DETECTOR,
                    category=FindingCategory.WHITEOUT,
                    severity=severity,
                    title=title,
                    description=(
                        f"A {rect['w']}×{rect['h']}px solid white rectangle "
                        f"(fill ratio {rect['fill_ratio']:.0%}) was detected. "
                        + (
                            f"It overlaps word(s): {overlapping_words[:5]}. "
                            if overlapping_words
                            else ""
                        )
                        + "White rectangles are used to conceal text in forged documents."
                    ),
                    page=page.page_number,
                    bbox={
                        "x0": round(x_pts, 1),
                        "y0": round(y_pts, 1),
                        "x1": round(x_pts + w_pts, 1),
                        "y1": round(y_pts + h_pts, 1),
                    },
                    evidence={
                        "rect_px": rect,
                        "overlapping_words": overlapping_words[:10],
                        "area_pts2": round(w_pts * h_pts, 1),
                    },
                )
            )

    return findings
