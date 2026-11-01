"""PDF text-layer extractor using pdfplumber + pikepdf.

Responsibilities:
  - Extract word tokens with bounding boxes from the native PDF text layer.
  - Pull font dictionaries from the PDF resource tree (pikepdf).
  - Extract embedded image regions.
  - Collect document-level metadata (title, author, producer, dates, etc.).
  - Compute SHA-256 hash of raw bytes.
  - Walk /Prev xref chain to count incremental revisions.

This module does NOT perform OCR. If a page has no text, `has_text_layer`
is set to False and the OCR router takes over.
"""

from __future__ import annotations

import contextlib
import hashlib
import re
from pathlib import Path
from typing import Any

from nirikshan.ingest.models import (
    BBox,
    FontInfo,
    ImageRegion,
    PageRecord,
    ParsedDocument,
    PDFMetadata,
    WordToken,
)

# Optional heavy imports — caught gracefully so tests can mock them
try:
    import pdfplumber
    _HAS_PDFPLUMBER = True
except ImportError:  # pragma: no cover
    _HAS_PDFPLUMBER = False

try:
    import pikepdf
    _HAS_PIKEPDF = True
except ImportError:  # pragma: no cover
    _HAS_PIKEPDF = False

# Minimum text characters on a page to consider the text layer "present"
_MIN_TEXT_CHARS = 20


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _count_revisions(raw_bytes: bytes) -> tuple[int, list[int]]:
    """Count incremental revisions by counting %%EOF markers.

    Also extract raw xref byte offsets from `startxref` lines.
    """
    eof_count = raw_bytes.count(b"%%EOF")
    revisions = max(1, eof_count)

    offsets: list[int] = []
    for m in re.finditer(rb"startxref\s+(\d+)", raw_bytes):
        with contextlib.suppress(ValueError):
            offsets.append(int(m.group(1)))

    return revisions, offsets


def _parse_metadata_pypdf(path: Path) -> PDFMetadata:
    """Fallback metadata extraction using pypdf (always available)."""
    from pypdf import PdfReader  # noqa: PLC0415

    meta = PDFMetadata(file_size_bytes=path.stat().st_size, sha256_hash=_sha256(path))
    with contextlib.suppress(Exception):
        reader = PdfReader(str(path), strict=False)
        info: dict[Any, Any] = dict(reader.metadata) if reader.metadata else {}
        meta.title = str(info.get("/Title", ""))
        meta.author = str(info.get("/Author", ""))
        meta.producer = str(info.get("/Producer", ""))
        meta.creator = str(info.get("/Creator", ""))
        meta.creation_date = str(info.get("/CreationDate", ""))
        meta.mod_date = str(info.get("/ModDate", ""))
        meta.subject = str(info.get("/Subject", ""))
        meta.keywords = str(info.get("/Keywords", ""))
        meta.page_count = len(reader.pages)
    return meta


def _extract_fonts_pikepdf(path: Path) -> dict[int, list[FontInfo]]:
    """Walk the pikepdf object tree and collect font dictionaries per page."""
    fonts_by_page: dict[int, list[FontInfo]] = {}
    if not _HAS_PIKEPDF:
        return fonts_by_page

    try:
        pdf = pikepdf.open(str(path))
    except Exception:
        return fonts_by_page

    with pdf:
        for page_idx, page_obj in enumerate(pdf.pages):
            page_num = page_idx + 1
            page_fonts: list[FontInfo] = []
            with contextlib.suppress(Exception):
                resources = page_obj.get("/Resources", pikepdf.Dictionary())
                font_dict = resources.get("/Font", pikepdf.Dictionary())
                for _key, font_ref in font_dict.items():
                    with contextlib.suppress(Exception):
                        font_obj = font_ref
                        name = str(font_obj.get("/BaseFont", ""))
                        subtype = str(font_obj.get("/Subtype", ""))
                        encoding = str(font_obj.get("/Encoding", ""))
                        embedded = "/FontDescriptor" in font_obj
                        page_fonts.append(
                            FontInfo(
                                name=name,
                                page=page_num,
                                is_embedded=embedded,
                                encoding=encoding,
                                subtype=subtype,
                            )
                        )
            fonts_by_page[page_num] = page_fonts

    return fonts_by_page


def _extract_page_images(plumber_page: Any, page_num: int, page_h: float) -> list[ImageRegion]:
    """Extract raster image bounding boxes from a pdfplumber page."""
    images: list[ImageRegion] = []
    try:
        for img in plumber_page.images:
            x0 = float(img.get("x0", 0))
            y0 = float(img.get("y0", 0))
            x1 = float(img.get("x1", x0))
            y1 = float(img.get("y1", y0))
            images.append(
                ImageRegion(
                    page=page_num,
                    bbox=BBox(x0=x0, y0=y0, x1=x1, y1=y1, page=page_num),
                    width_px=int(img.get("width", 0)),
                    height_px=int(img.get("height", 0)),
                    color_mode=img.get("colorspace", "RGB") or "RGB",
                )
            )
    except Exception:
        pass
    return images


def extract_pdf(path: Path) -> ParsedDocument:
    """Main entry point: parse a PDF file into a normalized ParsedDocument.

    Raises:
        FileNotFoundError: if path does not exist.
        RuntimeError: if neither pdfplumber nor pypdf can read the file.
    """
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    raw_bytes = path.read_bytes()
    rev_count, xref_offsets = _count_revisions(raw_bytes)

    # --- Metadata ---
    meta = _parse_metadata_pypdf(path)
    meta.sha256_hash = hashlib.sha256(raw_bytes).hexdigest()

    # --- Font dictionaries (pikepdf) ---
    fonts_by_page = _extract_fonts_pikepdf(path)

    # --- Pages (pdfplumber) ---
    pages: list[PageRecord] = []

    if not _HAS_PDFPLUMBER:
        # Minimal fallback: just create empty page records
        from pypdf import PdfReader  # noqa: PLC0415
        with contextlib.suppress(Exception):
            reader = PdfReader(str(path), strict=False)
            for i, _ in enumerate(reader.pages):
                pages.append(
                    PageRecord(
                        page_number=i + 1,
                        width_pts=595.0,
                        height_pts=842.0,
                        fonts=fonts_by_page.get(i + 1, []),
                        has_text_layer=False,
                    )
                )
    else:
        try:
            with pdfplumber.open(str(path)) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_num = i + 1
                    w = float(page.width)
                    h = float(page.height)

                    raw_words = page.extract_words(
                        x_tolerance=3,
                        y_tolerance=3,
                        extra_attrs=["fontname", "size"],
                    )
                    words: list[WordToken] = []
                    for wd in raw_words:
                        text = str(wd.get("text", "")).strip()
                        if not text:
                            continue
                        words.append(
                            WordToken(
                                text=text,
                                bbox=BBox(
                                    x0=float(wd.get("x0", 0)),
                                    y0=float(wd.get("top", 0)),
                                    x1=float(wd.get("x1", 0)),
                                    y1=float(wd.get("bottom", 0)),
                                    page=page_num,
                                ),
                                font_name=str(wd.get("fontname", "")),
                                font_size=float(wd.get("size", 0) or 0),
                            )
                        )

                    has_text = len("".join(w.text for w in words)) >= _MIN_TEXT_CHARS
                    images = _extract_page_images(page, page_num, h)

                    pages.append(
                        PageRecord(
                            page_number=page_num,
                            width_pts=w,
                            height_pts=h,
                            words=words,
                            fonts=fonts_by_page.get(page_num, []),
                            images=images,
                            has_text_layer=has_text,
                        )
                    )
        except Exception as exc:
            raise RuntimeError(f"pdfplumber failed to open {path}: {exc}") from exc

    return ParsedDocument(
        file_path=path,
        metadata=meta,
        pages=pages,
        revision_count=rev_count,
        has_incremental_updates=rev_count > 1,
        raw_xref_offsets=xref_offsets,
    )
