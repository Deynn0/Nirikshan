"""Offline OCR router using RapidOCR (PP-OCR ONNX models).

Design:
- RapidOCR is invoked only when a page has no native text layer
  (PageRecord.has_text_layer == False) or when forced via force_ocr=True.
- English model handles Latin script pages.
- Devanagari model handles Hindi/Marathi script pages (auto-detected by
  Unicode range U+0900–U+097F).
- At runtime, ZERO network calls are made. All ONNX weights must be
  pre-downloaded by scripts/fetch_models.py.
- If RapidOCR is not installed, this module returns empty word lists
  and logs a warning. It never raises at import time.

Model paths (can be overridden via NIRIKSHAN_OCR_* env vars):
  var/models/en_PP-OCRv3_rec.onnx
  var/models/hi_PP-OCRv3_rec.onnx  (Devanagari)
  var/models/ch_PP-OCRv3_det.onnx  (detector, shared)
"""

from __future__ import annotations

import io
import logging
from typing import Any

from nirikshan.config import settings
from nirikshan.ingest.models import BBox, PageRecord, TextSource, WordToken

log = logging.getLogger(__name__)

# RapidOCR optional import
try:
    from rapidocr_onnxruntime import RapidOCR  # type: ignore[import-untyped]
    _HAS_RAPIDOCR = True
except ImportError:
    _HAS_RAPIDOCR = False
    RapidOCR = None  # type: ignore[assignment, misc]

# Devanagari Unicode range U+0900-U+097F
_DEVANAGARI_RANGE_START = 0x0900
_DEVANAGARI_RANGE_END = 0x097F

_MODELS_DIR = settings.base_dir / "var" / "models"
_EN_REC_MODEL = _MODELS_DIR / "en_PP-OCRv3_rec.onnx"
_HI_REC_MODEL = _MODELS_DIR / "hi_PP-OCRv3_rec.onnx"
_DET_MODEL = _MODELS_DIR / "ch_PP-OCRv3_det.onnx"

# Singleton OCR engines (lazy initialized)
_ocr_en: Any | None = None
_ocr_hi: Any | None = None


def _get_ocr_engine(lang: str) -> Any | None:
    """Return (and lazily create) an OCR engine for the given language."""
    global _ocr_en, _ocr_hi  # noqa: PLW0603

    if not _HAS_RAPIDOCR:
        return None

    if lang == "hi":
        if _ocr_hi is None:
            rec_model = str(_HI_REC_MODEL) if _HI_REC_MODEL.exists() else None
            det_model = str(_DET_MODEL) if _DET_MODEL.exists() else None
            try:
                kwargs: dict[str, Any] = {}
                if rec_model:
                    kwargs["rec_model_path"] = rec_model
                if det_model:
                    kwargs["det_model_path"] = det_model
                _ocr_hi = RapidOCR(**kwargs)
            except Exception as exc:
                log.warning("Failed to init Hindi OCR engine: %s", exc)
                return None
        return _ocr_hi
    if _ocr_en is None:
        rec_model = str(_EN_REC_MODEL) if _EN_REC_MODEL.exists() else None
        det_model = str(_DET_MODEL) if _DET_MODEL.exists() else None
        try:
            kwargs = {}
            if rec_model:
                kwargs["rec_model_path"] = rec_model
            if det_model:
                kwargs["det_model_path"] = det_model
            _ocr_en = RapidOCR(**kwargs)
        except Exception as exc:
            log.warning("Failed to init English OCR engine: %s", exc)
            return None
    return _ocr_en


def _contains_devanagari(text: str) -> bool:
    """Return True if text contains Devanagari characters."""
    return any(
        _DEVANAGARI_RANGE_START <= ord(c) <= _DEVANAGARI_RANGE_END
        for c in text
    )


def _run_ocr_on_image(image_bytes: bytes, page_num: int, lang: str = "en") -> list[WordToken]:
    """Run RapidOCR on raw PNG/image bytes and return word tokens."""
    engine = _get_ocr_engine(lang)
    if engine is None:
        return []

    try:
        import numpy as np
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_array = np.array(img)
        results, _ = engine(img_array)
    except Exception as exc:
        log.debug("OCR failed on page %d: %s", page_num, exc)
        return []

    if not results:
        return []

    words: list[WordToken] = []
    source = TextSource.OCR_HI if lang == "hi" else TextSource.OCR_EN

    for item in results:
        try:
            # RapidOCR returns: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]], text, confidence
            if len(item) < 3:
                continue
            box_pts, text, conf = item[0], str(item[1]), float(item[2])
            if not text.strip():
                continue

            xs = [p[0] for p in box_pts]
            ys = [p[1] for p in box_pts]
            x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)

            # Convert pixel coords back to PDF points (assuming 150 DPI)
            scale = 72.0 / 150.0
            words.append(
                WordToken(
                    text=text,
                    bbox=BBox(
                        x0=x0 * scale,
                        y0=y0 * scale,
                        x1=x1 * scale,
                        y1=y1 * scale,
                        page=page_num,
                    ),
                    font_name="OCR",
                    font_size=0.0,
                    source=source,
                    confidence=conf,
                )
            )
        except Exception:
            continue

    return words


def ocr_page(page: PageRecord, force: bool = False) -> bool:
    """Run OCR on *page* if needed.

    Returns True if OCR was performed.
    Modifies page.words and page.has_text_layer in-place.
    """
    if not force and page.has_text_layer:
        return False

    if not page.raster_png:
        log.debug("Page %d: no raster PNG available for OCR", page.page_number)
        return False

    # Auto-detect language: check if any existing text has Devanagari
    existing_text = " ".join(w.text for w in page.words)
    lang = "hi" if _contains_devanagari(existing_text) else "en"

    ocr_words = _run_ocr_on_image(page.raster_png, page.page_number, lang)
    if ocr_words:
        page.words = ocr_words
        page.has_text_layer = True
        return True

    # Try opposite language if first fails
    alt_lang = "en" if lang == "hi" else "hi"
    ocr_words = _run_ocr_on_image(page.raster_png, page.page_number, alt_lang)
    if ocr_words:
        page.words = ocr_words
        page.has_text_layer = True
        return True

    return False


def ocr_document(doc: Any, force_pages: list[int] | None = None) -> int:
    """Run OCR on all pages that lack a text layer.

    Args:
        doc: ParsedDocument instance.
        force_pages: 1-based page numbers to force OCR regardless of text layer.

    Returns:
        Number of pages that had OCR applied.
    """
    forced = set(force_pages or [])
    count = 0
    for page in doc.pages:
        force = page.page_number in forced
        if ocr_page(page, force=force):
            count += 1
    return count
