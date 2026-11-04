"""Core Pipeline & Foundation: Standalone document analysis, bounded memory store, timeouts.

Covers:
- Standalone document parsing & ingestion (text extraction, bbox mapping, word tokens, xref offsets)
- Bounded memory store & sandbox resource limits (infinite loop timeout, decompression bomb ratio cap, page count cap, file size cap)
- Strict quarantine and network airgap isolation
"""

from __future__ import annotations

import io
import socket
import zlib
from pathlib import Path

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas

from nirikshan.config import settings
from nirikshan.ingest.models import BBox, PageRecord, ParsedDocument, PDFMetadata, WordToken
from nirikshan.ingest.pdf_extractor import extract_pdf
from nirikshan.ingest.pipeline import ingest_pdf
from nirikshan.sandbox import (
    SandboxedWorkerManager,
    SandboxViolationError,
    SandboxViolationType,
    _check_decompression_ratio,
    _check_page_count_fast,
)


def _pdf_bytes(**kwargs) -> bytes:
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)
    for text, y in kwargs.get("texts", [("Sample regulatory text.", 780)]):
        c.setFont("Helvetica", 12)
        c.drawString(72, y, text)
    c.showPage()
    if kwargs.get("page2"):
        c.drawString(72, 780, "Page 2 content.")
        c.showPage()
    c.save()
    return buf.getvalue()


@pytest.fixture
def clean_pdf(tmp_path: Path) -> Path:
    data = _pdf_bytes(
        texts=[
            ("AICTE Regulatory Document", 800),
            ("Land area: 5.2 acres. Survey No: 123/4A.", 780),
            ("Fire NOC valid until 2025-12-31.", 760),
        ],
        page2=True,
    )
    p = tmp_path / "clean.pdf"
    p.write_bytes(data)
    return p


# ---------------------------------------------------------------------------
# Standalone Document Parsing & Ingestion
# ---------------------------------------------------------------------------

def test_page_record_and_tokens() -> None:
    page = PageRecord(page_number=1, width_pts=595, height_pts=842)
    page.words = [
        WordToken("Approval", BBox(0, 0, 50, 12, 1)),
        WordToken("Process", BBox(55, 0, 100, 12, 1)),
    ]
    assert page.text == "Approval Process"

    doc = ParsedDocument(file_path=Path("."), metadata=PDFMetadata())
    doc.pages = [page]
    assert len(doc.all_words) == 2


def test_extract_pdf_basic_and_offsets(clean_pdf: Path) -> None:
    doc = extract_pdf(clean_pdf)
    assert len(doc.pages) >= 1
    assert doc.metadata.sha256_hash != ""
    assert doc.metadata.file_size_bytes > 0
    assert len(doc.full_text) >= 10
    assert doc.revision_count >= 1
    assert len(doc.raw_xref_offsets) >= 1


def test_pipeline_no_raster(clean_pdf: Path) -> None:
    doc = ingest_pdf(clean_pdf, enable_raster=False, enable_ocr=False)
    assert len(doc.pages) >= 1
    assert doc.pages[0].raster_png == b""


def test_pipeline_with_raster(clean_pdf: Path) -> None:
    doc = ingest_pdf(clean_pdf, enable_raster=True, enable_ocr=False)
    assert len(doc.pages) >= 1


# ---------------------------------------------------------------------------
# Bounded Memory Store & Timeouts
# ---------------------------------------------------------------------------

def test_sandbox_infinite_loop_timeout() -> None:
    mgr = SandboxedWorkerManager(wall_clock_timeout=2)
    infinite_loop_code = (
        "import time\n"
        "while True:\n"
        "    time.sleep(0.1)\n"
    )

    with pytest.raises(SandboxViolationError) as exc_info:
        mgr.run_isolated_code(infinite_loop_code, timeout=2.0)

    err = exc_info.value
    assert err.violation_type in (
        SandboxViolationType.TIMEOUT_EXCEEDED,
        SandboxViolationType.CPU_LIMIT_EXCEEDED,
    )


def test_sandbox_zip_bomb_decompression_ratio() -> None:
    repeated_content = b"AICTE-REGULATORY-SCRUTINY-" * 8000
    compressed_stream = zlib.compress(repeated_content, level=9)
    assert len(compressed_stream) < 1000

    synthetic_pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj\n"
        b"<< /Length 400 /Filter /FlateDecode >>\n"
        b"stream\n" + compressed_stream + b"\nendstream\n"
        b"endobj\n"
        b"%%EOF\n"
    )

    with pytest.raises(SandboxViolationError) as exc_info:
        _check_decompression_ratio(synthetic_pdf_bytes, max_ratio=20.0)

    err = exc_info.value
    assert err.violation_type == SandboxViolationType.DECOMPRESSION_BOMB
    assert err.details["ratio"] > 20.0


def test_sandbox_page_count_cap() -> None:
    pages_raw = b"".join(
        f"{i} 0 obj << /Type /Page >> endobj\n".encode() for i in range(1, 151)
    )
    pdf_bytes = b"%PDF-1.4\n" + pages_raw + b"%%EOF\n"

    with pytest.raises(SandboxViolationError) as exc_info:
        _check_page_count_fast(pdf_bytes, max_pages=100)

    err = exc_info.value
    assert err.violation_type == SandboxViolationType.PAGE_COUNT_EXCEEDED


def test_sandbox_file_size_cap(tmp_path: Path) -> None:
    test_file = tmp_path / "oversized.pdf"
    test_file.write_bytes(b"x" * 1024)

    mgr = SandboxedWorkerManager(max_file_size_bytes=500)
    with pytest.raises(SandboxViolationError) as exc_info:
        mgr.validate_file_guards(test_file)

    err = exc_info.value
    assert err.violation_type == SandboxViolationType.FILE_SIZE_EXCEEDED
    assert err.details["file_size"] == 1024


# ---------------------------------------------------------------------------
# Strict Quarantine & Network Isolation
# ---------------------------------------------------------------------------

def test_sandbox_network_isolation() -> None:
    mgr = SandboxedWorkerManager(wall_clock_timeout=5)
    network_code = (
        "import socket\n"
        "s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
        "s.connect(('1.1.1.1', 80))\n"
    )

    with pytest.raises(SandboxViolationError) as exc_info:
        mgr.run_isolated_code(network_code, timeout=5.0)

    err = exc_info.value
    assert err.violation_type == SandboxViolationType.NETWORK_ACCESS_BLOCKED


def test_constitution_airgap_blocks_external_network() -> None:
    assert settings.allow_external_network is False

    from nirikshan.main import _install_airgap_guard
    _install_airgap_guard()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(PermissionError) as exc_info:
            s.connect(("8.8.8.8", 53))
        assert "Airgap Violation" in str(exc_info.value)
    finally:
        s.close()
