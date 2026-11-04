"""Digital Forensics & Document Integrity: PDF annotations, white-outs, scribble layers, incremental edits."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas

from nirikshan.forensics import revision_detector, whiteout_detector
from nirikshan.ingest.pdf_extractor import extract_pdf
from nirikshan.ingest.rasterizer import rasterize_document


def _pdf_bytes(**kwargs) -> bytes:
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)
    for text, y in kwargs.get("texts", [("Sample regulatory text.", 780)]):
        c.setFont("Helvetica", 12)
        c.drawString(72, y, text)
    for rect in kwargs.get("white_rects", []):
        c.setFillColorRGB(1, 1, 1)
        x, y, w, h = rect
        c.rect(x, y, w, h, fill=1, stroke=0)
    c.showPage()
    if kwargs.get("page2"):
        c.drawString(72, 780, "Page 2 content.")
        c.showPage()
    c.save()
    raw = buf.getvalue()
    inject = kwargs.get("inject_bytes", b"")
    if inject:
        raw = raw.replace(b"%%EOF", inject + b"\n%%EOF", 1)
    return raw


@pytest.fixture
def clean_pdf(tmp_path: Path) -> Path:
    data = _pdf_bytes(
        texts=[
            ("AICTE Regulatory Document", 800),
            ("Land area: 5.2 acres. Survey No: 123/4A.", 780),
        ],
        page2=True,
    )
    p = tmp_path / "clean.pdf"
    p.write_bytes(data)
    return p


@pytest.fixture
def js_pdf(tmp_path: Path) -> Path:
    data = _pdf_bytes(texts=[("Test document.", 780)])
    data = data.replace(b"%%EOF", b"/JavaScript (alert(1))\n%%EOF", 1)
    p = tmp_path / "js_tampered.pdf"
    p.write_bytes(data)
    return p


@pytest.fixture
def whiteout_pdf(tmp_path: Path) -> Path:
    data = _pdf_bytes(
        texts=[("Survey No: 999/1B", 780)],
        white_rects=[(70, 775, 200, 20)],
    )
    p = tmp_path / "whiteout.pdf"
    p.write_bytes(data)
    return p


def test_clean_pdf_no_critical(clean_pdf: Path) -> None:
    doc = extract_pdf(clean_pdf)
    findings = revision_detector.detect(doc)
    critical = [f for f in findings if f.severity == "CRITICAL"]
    assert len(critical) == 0


def test_js_pdf_detected(js_pdf: Path) -> None:
    doc = extract_pdf(js_pdf)
    findings = revision_detector.detect(doc)
    titles = [f.title for f in findings]
    assert any("JavaScript" in t for t in titles)


def test_incremental_updates_flagged(tmp_path: Path) -> None:
    data = _pdf_bytes(texts=[("doc", 780)])
    data = data + b"\n%%EOF\n%%EOF\n%%EOF\n%%EOF\n%%EOF"
    pdf_path = tmp_path / "multi_eof.pdf"
    pdf_path.write_bytes(data)
    doc = extract_pdf(pdf_path)
    findings = revision_detector.detect(doc)
    rev_findings = [f for f in findings if f.category == "REVISION"]
    assert len(rev_findings) >= 1


def test_launch_detected(tmp_path: Path) -> None:
    data = _pdf_bytes(texts=[("doc", 780)])
    data = data.replace(b"%%EOF", b"/Launch\n%%EOF", 1)
    p = tmp_path / "launch.pdf"
    p.write_bytes(data)
    doc = extract_pdf(p)
    findings = revision_detector.detect(doc)
    assert any("Launch" in f.title for f in findings)


def test_no_raster_no_whiteout_findings(clean_pdf: Path) -> None:
    doc = extract_pdf(clean_pdf)
    for p in doc.pages:
        p.raster_png = b""
    findings = whiteout_detector.detect(doc)
    assert isinstance(findings, list)


def test_whiteout_pdf_with_raster(whiteout_pdf: Path) -> None:
    doc = extract_pdf(whiteout_pdf)
    rasterize_document(doc)
    findings = whiteout_detector.detect(doc)
    assert isinstance(findings, list)


def test_annotation_layers_inspection(clean_pdf: Path) -> None:
    doc = extract_pdf(clean_pdf)
    assert doc.pages[0].page_number == 1
    assert isinstance(doc.pages[0].words, list)

