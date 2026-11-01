"""Full document ingest pipeline: parse → rasterize → OCR fallback.

This is the single entry point for all document ingestion.
Usage:
    from nirikshan.ingest.pipeline import ingest_pdf
    doc = ingest_pdf(Path("file.pdf"))
"""

from __future__ import annotations

import logging
from pathlib import Path

from nirikshan.ingest.models import ParsedDocument
from nirikshan.ingest.ocr_router import ocr_document
from nirikshan.ingest.pdf_extractor import extract_pdf
from nirikshan.ingest.rasterizer import rasterize_document

log = logging.getLogger(__name__)


def ingest_pdf(
    path: Path,
    *,
    dpi: int = 150,
    enable_ocr: bool = True,
    enable_raster: bool = True,
) -> ParsedDocument:
    """Full pipeline: PDF extract → rasterize → OCR fallback.

    Args:
        path: Absolute path to the PDF file.
        dpi: Rasterization DPI (default 150).
        enable_ocr: Run OCR on pages with no text layer.
        enable_raster: Render pages to PNG bytes.

    Returns:
        Populated ParsedDocument.
    """
    log.info("Ingesting PDF: %s", path.name)

    # Step 1: PDF text extraction
    doc = extract_pdf(path)
    log.debug("Extracted %d pages, %d words total", len(doc.pages), len(doc.all_words))

    # Step 2: Page rasterization (required for OCR and visual forensics)
    if enable_raster:
        rasterize_document(doc, dpi=dpi)
        log.debug("Rasterized %d pages at %d DPI", len(doc.pages), dpi)

    # Step 3: OCR fallback for scanned / garbled pages
    if enable_ocr:
        ocr_count = ocr_document(doc)
        if ocr_count:
            log.info("OCR applied to %d page(s) in %s", ocr_count, path.name)

    return doc
