"""Page rasterizer using pypdfium2.

Renders each PDF page to a PNG at a configurable DPI (default 150 DPI).
The raster bytes are stored in PageRecord.raster_png for:
  - Whiteout detection (OpenCV)
  - Seal/stamp detection (OpenCV + imagehash)
  - OCR input (RapidOCR)
  - Revision Time Machine (visual diff)

This module is optional: if pypdfium2 is not installed, pages fall back
to empty raster_png bytes and callers must handle that gracefully.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nirikshan.ingest.models import ParsedDocument

try:
    import pypdfium2 as pdfium

    _HAS_PDFIUM = True
except ImportError:  # pragma: no cover
    _HAS_PDFIUM = False

DEFAULT_DPI = 150
_SCALE = DEFAULT_DPI / 72.0  # PDF points → pixels


def rasterize_document(doc: ParsedDocument, dpi: int = DEFAULT_DPI) -> None:
    """Render every page of *doc* to PNG bytes, stored in-place.

    Modifies doc.pages[i].raster_png in-place.
    Safe to call even if pypdfium2 is unavailable (pages get empty bytes).
    """
    if not _HAS_PDFIUM:
        return  # pragma: no cover

    scale = dpi / 72.0
    try:
        pdf = pdfium.PdfDocument(str(doc.file_path))
    except Exception:
        return

    try:
        for page_rec in doc.pages:
            idx = page_rec.page_number - 1
            if idx >= len(pdf):
                continue
            try:
                page = pdf[idx]
                bitmap = page.render(scale=scale, rotation=0)
                pil_img = bitmap.to_pil()
                buf = io.BytesIO()
                pil_img.save(buf, format="PNG", optimize=False)
                page_rec.raster_png = buf.getvalue()
            except Exception:
                pass  # leave raster_png empty
    finally:
        pdf.close()


def rasterize_file(path: Path, page_numbers: list[int] | None = None, dpi: int = DEFAULT_DPI) -> dict[int, bytes]:
    """Render specific pages (1-based) from *path* to PNG bytes dict.

    Returns {page_number: png_bytes}. Useful for the Revision Time Machine.
    """
    result: dict[int, bytes] = {}
    if not _HAS_PDFIUM:
        return result  # pragma: no cover

    scale = dpi / 72.0
    try:
        pdf = pdfium.PdfDocument(str(path))
    except Exception:
        return result

    try:
        target = page_numbers if page_numbers else list(range(1, len(pdf) + 1))
        for page_num in target:
            idx = page_num - 1
            if idx < 0 or idx >= len(pdf):
                continue
            try:
                page = pdf[idx]
                bitmap = page.render(scale=scale, rotation=0)
                pil_img = bitmap.to_pil()
                buf = io.BytesIO()
                pil_img.save(buf, format="PNG")
                result[page_num] = buf.getvalue()
            except Exception:
                pass
    finally:
        pdf.close()

    return result
