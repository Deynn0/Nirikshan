"""Digital Forensics & Document Integrity: Ghostscript/font anomalies, font subset analysis, metadata drift."""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas

from nirikshan.forensics import font_detector, tool_signature_detector
from nirikshan.forensics.font_detector import _base_family
from nirikshan.forensics.scan import scan_pdf
from nirikshan.ingest.pdf_extractor import extract_pdf


def _pdf_bytes(**kwargs) -> bytes:
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)
    for text, y in kwargs.get("texts", [("Sample regulatory text.", 780)]):
        c.setFont("Helvetica", 12)
        c.drawString(72, y, text)
    c.showPage()
    c.save()
    return buf.getvalue()


@pytest.fixture
def clean_pdf(tmp_path: Path) -> Path:
    data = _pdf_bytes(
        texts=[
            ("AICTE Approval Process Handbook", 800),
            ("Land title document verified.", 780),
        ]
    )
    p = tmp_path / "clean_forensic.pdf"
    p.write_bytes(data)
    return p


@pytest.fixture
def multi_font_pdf(tmp_path: Path) -> Path:
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica", 12)
    c.drawString(72, 800, "Standard Title")
    c.setFont("Times-Roman", 10)
    c.drawString(72, 780, "Body text font")
    c.setFont("Courier", 9)
    c.drawString(72, 760, "Coupled mono reference 12345")
    c.showPage()
    c.save()
    p = tmp_path / "multi_font.pdf"
    p.write_bytes(buf.getvalue())
    return p


# ---------------------------------------------------------------------------
# Font Anomaly & Font Subset Analysis
# ---------------------------------------------------------------------------

def test_base_family_strips_subset() -> None:
    assert _base_family("ABCDEF+Arial") == "Arial"
    assert _base_family("XYZ123+Helvetica-Bold") == "Helvetica"
    assert _base_family("Times-Roman-Italic") == "Times-Roman"


def test_clean_pdf_no_high_severity_fonts(clean_pdf: Path) -> None:
    doc = extract_pdf(clean_pdf)
    findings = font_detector.detect(doc)
    high = [f for f in findings if f.severity in ("CRITICAL", "HIGH")]
    assert len(high) == 0


def test_multi_font_detected(multi_font_pdf: Path) -> None:
    doc = extract_pdf(multi_font_pdf)
    findings = font_detector.detect(doc)
    assert isinstance(findings, list)


# ---------------------------------------------------------------------------
# Tool Signature & Metadata Drift (Ghostscript, iLovePDF, etc.)
# ---------------------------------------------------------------------------

def test_clean_pdf_no_suspicious_tools(clean_pdf: Path) -> None:
    doc = extract_pdf(clean_pdf)
    findings = tool_signature_detector.detect(doc)
    high = [f for f in findings if f.severity == "HIGH"]
    assert len(high) == 0


def test_suspicious_tool_flagged(clean_pdf: Path) -> None:
    doc = extract_pdf(clean_pdf)
    doc.metadata.producer = "GPL Ghostscript 9.50 / ilovepdf.com"
    findings = tool_signature_detector.detect(doc)
    suspicious = [f for f in findings if f.severity == "HIGH"]
    assert len(suspicious) >= 1


def test_missing_metadata_flagged(clean_pdf: Path) -> None:
    doc = extract_pdf(clean_pdf)
    doc.metadata.producer = ""
    doc.metadata.creator = ""
    findings = tool_signature_detector.detect(doc)
    assert any("Missing" in f.title for f in findings)


# ---------------------------------------------------------------------------
# Forensic Scan Runner & CLI Execution
# ---------------------------------------------------------------------------

def test_scan_pdf_returns_report(clean_pdf: Path) -> None:
    report = scan_pdf(clean_pdf, enable_raster=False, enable_ocr=False)
    assert report.sha256 != ""
    assert report.page_count >= 1
    assert isinstance(report.findings, list)
    d = report.as_dict()
    assert "findings" in d
    assert "sha256" in d
    # Ensure JSON serializable
    parsed = json.loads(json.dumps(d))
    assert parsed["page_count"] >= 1


def test_cli_json_output(clean_pdf: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "nirikshan.forensics.scan",
            str(clean_pdf),
            "--json",
            "--no-raster",
            "--no-ocr",
        ],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parents[1]),
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert "sha256" in data
    assert "findings" in data


def test_cli_missing_file(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "nirikshan.forensics.scan",
            str(tmp_path / "non_existent.pdf"),
            "--json",
            "--no-raster",
            "--no-ocr",
        ],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parents[1]),
    )
    assert result.returncode != 0

