"""Normalized document model output from the ingest pipeline.

ParsedDocument is the central data contract between:
  - PDF parsing (pdfplumber + pikepdf + pypdfium2)
  - OCR fallback (RapidOCR)
  - Forensic detectors
  - Rule engine evidence layer

Everything is page-indexed (1-based) to match PDF conventions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class TextSource(StrEnum):
    """Origin of a word's text content."""

    PDF_LAYER = "PDF_LAYER"    # native text from PDF content stream
    OCR_EN = "OCR_EN"          # RapidOCR English (PP-OCR ONNX)
    OCR_HI = "OCR_HI"          # RapidOCR Devanagari model
    SYNTHETIC = "SYNTHETIC"    # injected by tests / fixtures


@dataclass
class BBox:
    """Bounding box in PDF points (1pt = 1/72 inch), origin = bottom-left."""

    x0: float
    y0: float
    x1: float
    y1: float
    page: int  # 1-based

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    def as_dict(self) -> dict[str, Any]:
        return {"x0": self.x0, "y0": self.y0, "x1": self.x1, "y1": self.y1, "page": self.page}


@dataclass
class WordToken:
    """A single word extracted from the document with positional metadata."""

    text: str
    bbox: BBox
    font_name: str = ""
    font_size: float = 0.0
    source: TextSource = TextSource.PDF_LAYER
    confidence: float = 1.0  # 0.0-1.0; 1.0 for native PDF layer


@dataclass
class FontInfo:
    """Per-page font summary."""

    name: str
    page: int  # 1-based
    is_embedded: bool = True
    encoding: str = ""
    subtype: str = ""  # Type1, TrueType, CIDFont, etc.


@dataclass
class ImageRegion:
    """Raster image embedded on a page."""

    page: int  # 1-based
    bbox: BBox
    width_px: int
    height_px: int
    color_mode: str = "RGB"   # RGB / RGBA / L / CMYK
    data: bytes = field(default_factory=bytes, repr=False)


@dataclass
class PageRecord:
    """All extracted content for one PDF page."""

    page_number: int         # 1-based
    width_pts: float
    height_pts: float
    words: list[WordToken] = field(default_factory=list)
    fonts: list[FontInfo] = field(default_factory=list)
    images: list[ImageRegion] = field(default_factory=list)
    raster_png: bytes = field(default_factory=bytes, repr=False)  # page rendered at 150 DPI
    has_text_layer: bool = True  # False → OCR was used

    @property
    def text(self) -> str:
        """Full page text joined by spaces."""
        return " ".join(w.text for w in self.words)


@dataclass
class PDFMetadata:
    """Extracted PDF document-level metadata."""

    title: str = ""
    author: str = ""
    producer: str = ""
    creator: str = ""
    creation_date: str = ""
    mod_date: str = ""
    subject: str = ""
    keywords: str = ""
    # xmp fields
    xmp_metadata: dict[str, str] = field(default_factory=dict)
    page_count: int = 0
    file_size_bytes: int = 0
    sha256_hash: str = ""


@dataclass
class ParsedDocument:
    """Full normalized parse output for a PDF file.

    This is the single output model of the ingest pipeline and the
    primary input to all forensic detectors.
    """

    file_path: Path
    metadata: PDFMetadata
    pages: list[PageRecord] = field(default_factory=list)

    # Raw revision history (populated by revision detector)
    revision_count: int = 0
    has_incremental_updates: bool = False

    # Raw pikepdf object stream bytes (opaque, for forensic tools)
    raw_xref_offsets: list[int] = field(default_factory=list)

    @property
    def all_words(self) -> list[WordToken]:
        return [w for p in self.pages for w in p.words]

    @property
    def all_fonts(self) -> list[FontInfo]:
        return [f for p in self.pages for f in p.fonts]

    @property
    def full_text(self) -> str:
        return "\n".join(p.text for p in self.pages)
