"""Unit tests for PDFAnalyzer forensic edge case detection."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas

from nirikshan.parsers.pdf_parser import pdf_analyzer
from nirikshan.trust.ladder import TrustLevel


def _make_pdf_bytes(
    texts: list[str] | None = None,
    producer: str | None = None,
    creator: str | None = None,
) -> bytes:
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)
    if producer:
        c.setProducer(producer)
    if creator:
        c.setCreator(creator)
    y = 800
    for t in texts or ["Sample Regulatory Document"]:
        c.drawString(72, y, t)
        y -= 25
    c.showPage()
    c.save()
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 1. Zero-byte and Corrupt Header Edge Cases
# ---------------------------------------------------------------------------

def test_zero_byte_file(tmp_path: Path) -> None:
    p = tmp_path / "empty.pdf"
    p.write_bytes(b"")
    report, preview, params = pdf_analyzer.analyze_file(p, "doc-empty")
    assert report.is_tampered is True
    assert any("empty" in flag.lower() for flag in report.tamper_flags)
    assert report.assessed_trust_level == TrustLevel.STRUCTURAL_FORENSIC


def test_corrupt_header(tmp_path: Path) -> None:
    p = tmp_path / "corrupt_header.pdf"
    p.write_bytes(b"NOT_A_PDF_STREAM_RANDOM_DATA_12345")
    report, preview, params = pdf_analyzer.analyze_file(p, "doc-corrupt")
    assert report.is_tampered is True
    assert any("header" in flag.lower() or "parsing" in flag.lower() for flag in report.tamper_flags)


# ---------------------------------------------------------------------------
# 2. Dangerous Actions & Script Triggers Edge Cases
# ---------------------------------------------------------------------------

def test_javascript_action_flagged(tmp_path: Path) -> None:
    base = _make_pdf_bytes(["Test document"])
    tampered = base + b"\n% Tamper Stream\n/JavaScript (app.alert('pwned'));\n%%EOF\n"
    p = tmp_path / "js.pdf"
    p.write_bytes(tampered)

    report, _, _ = pdf_analyzer.analyze_file(p, "doc-js")
    assert report.is_tampered is True
    assert any("javascript" in f.lower() for f in report.tamper_flags)


def test_launch_action_flagged(tmp_path: Path) -> None:
    base = _make_pdf_bytes(["Test document"])
    tampered = base + b"\n/Launch << /F (cmd.exe) >>\n%%EOF\n"
    p = tmp_path / "launch.pdf"
    p.write_bytes(tampered)

    report, _, _ = pdf_analyzer.analyze_file(p, "doc-launch")
    assert report.is_tampered is True
    assert any("launch" in f.lower() for f in report.tamper_flags)


def test_embedded_files_flagged(tmp_path: Path) -> None:
    base = _make_pdf_bytes(["Test document"])
    tampered = base + b"\n/EmbeddedFiles << /Names [(payload.exe)] >>\n%%EOF\n"
    p = tmp_path / "embed.pdf"
    p.write_bytes(tampered)

    report, _, _ = pdf_analyzer.analyze_file(p, "doc-embed")
    assert report.is_tampered is True
    assert any("embeddedfiles" in f.lower() for f in report.tamper_flags)


# ---------------------------------------------------------------------------
# 3. Tool Signature Detection Edge Cases
# ---------------------------------------------------------------------------

def test_suspicious_tool_ilovepdf(tmp_path: Path) -> None:
    data = _make_pdf_bytes(["Affidavit Text"], producer="iLovePDF Online Suite v3.2")
    p = tmp_path / "ilovepdf.pdf"
    p.write_bytes(data)

    report, _, _ = pdf_analyzer.analyze_file(p, "doc-tool")
    assert report.is_tampered is True
    assert any("ilovepdf" in f.lower() for f in report.tamper_flags)


def test_suspicious_tool_canva(tmp_path: Path) -> None:
    data = _make_pdf_bytes(["Land Title"], creator="Canva Design Studio")
    p = tmp_path / "canva.pdf"
    p.write_bytes(data)

    report, _, _ = pdf_analyzer.analyze_file(p, "doc-canva")
    assert report.is_tampered is True
    assert any("canva" in f.lower() for f in report.tamper_flags)


def test_downgraded_acrobat_tool(tmp_path: Path) -> None:
    data = _make_pdf_bytes(["Sanctioned Plan"], producer="Acrobat Distiller 4.0 for Windows")
    p = tmp_path / "acrobat4.pdf"
    p.write_bytes(data)

    report, _, _ = pdf_analyzer.analyze_file(p, "doc-acro")
    assert report.is_tampered is True
    assert any("legacy downgraded" in f.lower() or "acrobat" in f.lower() for f in report.tamper_flags)


# ---------------------------------------------------------------------------
# 4. Whiteout / Masking Overlays Edge Cases
# ---------------------------------------------------------------------------

def test_whiteout_square_annotation_overlay(tmp_path: Path) -> None:
    base = _make_pdf_bytes(["Official Land Deed"])
    tampered = base + b"\n3 0 obj\n<< /Type /Annot /Subtype /Square /Rect [100 200 300 250] /IC [ 1 1 1 ] >>\nendobj\n%%EOF\n"
    p = tmp_path / "whiteout.pdf"
    p.write_bytes(tampered)

    report, _, _ = pdf_analyzer.analyze_file(p, "doc-whiteout")
    assert report.is_tampered is True
    assert any("whiteout" in f.lower() for f in report.tamper_flags)


def test_redaction_annotation_overlay(tmp_path: Path) -> None:
    base = _make_pdf_bytes(["Official Land Deed"])
    tampered = base + b"\n4 0 obj\n<< /Type /Annot /Subtype /Redact /Rect [50 50 150 80] >>\nendobj\n%%EOF\n"
    p = tmp_path / "redact.pdf"
    p.write_bytes(tampered)

    report, _, _ = pdf_analyzer.analyze_file(p, "doc-redact")
    assert report.is_tampered is True
    assert any("redact" in f.lower() for f in report.tamper_flags)


# ---------------------------------------------------------------------------
# 5. Digital Signature & Post-Signature Incremental Append (ByteRange Edge Case)
# ---------------------------------------------------------------------------

def test_post_signature_incremental_modification(tmp_path: Path) -> None:
    # Construct a synthetic PDF with a valid-looking /ByteRange where file has extra appended bytes
    header = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    sig_obj = b"5 0 obj\n<< /Type /Sig /ByteRange [ 0 100 200 300 ] /Filter /Adobe.PPKLite >>\nendobj\n%%EOF\n"
    initial_content = header + sig_obj
    signed_length = len(initial_content)

    # Now append an unauthorized incremental modification (tampering with numbers post-sign)
    post_sign_append = b"\n% Unauthorized Incremental Append\n10 0 obj\n<< /CarpetArea 9999 >>\nendobj\n%%EOF\n"
    # Make sure ByteRange indicates signed_boundary is smaller than total file size
    br_str = f"/ByteRange [ 0 50 60 {signed_length - 60} ]".encode("ascii")
    raw_pdf = initial_content.replace(b"/ByteRange [ 0 100 200 300 ]", br_str) + post_sign_append

    p = tmp_path / "tampered_post_sign.pdf"
    p.write_bytes(raw_pdf)

    report, _, _ = pdf_analyzer.analyze_file(p, "doc-post-sign")
    assert report.has_digital_signature is True
    assert report.is_tampered is True
    assert any("modified post-sign" in f.lower() for f in report.tamper_flags)
    assert report.assessed_trust_level == TrustLevel.STRUCTURAL_FORENSIC


# ---------------------------------------------------------------------------
# 6. Hidden Trailing Data after %%EOF Edge Case
# ---------------------------------------------------------------------------

def test_hidden_trailing_payload(tmp_path: Path) -> None:
    base = _make_pdf_bytes(["Normal File"])
    hidden_payload = b"X" * 200  # 200 bytes of secret data appended after %%EOF
    p = tmp_path / "trailing.pdf"
    p.write_bytes(base + b"\n" + hidden_payload)

    report, _, _ = pdf_analyzer.analyze_file(p, "doc-trailing")
    assert report.is_tampered is True
    assert any("hidden trailing payload" in f.lower() for f in report.tamper_flags)


# ---------------------------------------------------------------------------
# 7. Font Anomalies & Type3 Fonts Edge Case
# ---------------------------------------------------------------------------

def test_type3_font_declaration_flagged(tmp_path: Path) -> None:
    base = _make_pdf_bytes(["Faculty Certificate"])
    tampered = base + b"\n7 0 obj\n<< /Type /Font /Subtype /Type3 /FontBBox [0 0 1000 1000] >>\nendobj\n%%EOF\n"
    p = tmp_path / "type3.pdf"
    p.write_bytes(tampered)

    report, _, _ = pdf_analyzer.analyze_file(p, "doc-type3")
    assert any("type3" in a.lower() for a in report.font_anomalies)


# ---------------------------------------------------------------------------
# 8. Regulatory Parameter Extraction Edge Cases
# ---------------------------------------------------------------------------

def test_parameter_extraction_acres_and_survey(tmp_path: Path) -> None:
    data = _make_pdf_bytes([
        "Government of Maharashtra Revenue Department",
        "Registered Sale Deed for Land Area 7.5 Acres",
        "Survey No: 44/2A Plot 9",
        "Built-up area: 4850 sq.m approved DTCP",
        "FDR of Rs. 45.0 Lakhs deposited jointly with AICTE",
        "Total Faculty Count: 24 (Professors: 3, Assoc. Professors: 6, Asst. Professors: 15)",
        "Trust Registration No: F-18492/Pune",
    ])
    p = tmp_path / "reg_doc.pdf"
    p.write_bytes(data)

    report, preview, params = pdf_analyzer.analyze_file(p, "doc-reg")
    assert params.get("land_area_acres") == 7.5
    assert params.get("survey_no") == "44/2A"
    assert params.get("built_up_area_sqm") == 4850.0
    assert params.get("fdr_amount_lakhs") == 45.0
    assert params.get("faculty_count") == 24
    assert params.get("cadre_professors") == 3
    assert params.get("cadre_assoc_professors") == 6
    assert params.get("cadre_asst_professors") == 15
    assert params.get("trust_registration_no") == "F-18492/PUNE"


def test_parameter_extraction_hectares_conversion(tmp_path: Path) -> None:
    # 2.0 Hectares = 2.0 * 2.47105 = 4.942 acres
    data = _make_pdf_bytes([
        "Agricultural Land Conversion NA Order",
        "Total land parcel measuring 2.0 Hectares",
        "Khasra No: 104/1B",
    ])
    p = tmp_path / "ha_doc.pdf"
    p.write_bytes(data)

    _, _, params = pdf_analyzer.analyze_file(p, "doc-ha")
    assert params.get("land_area_acres") == 4.942
    assert params.get("survey_no") == "104/1B"


def test_parameter_extraction_guntha_conversion(tmp_path: Path) -> None:
    # 160 Guntha = 160 / 40 = 4.0 acres
    data = _make_pdf_bytes([
        "Sub-Registrar 30 Year Lease Deed",
        "Land parcel area 160 Guntha situated at Gat No: 78",
    ])
    p = tmp_path / "guntha_doc.pdf"
    p.write_bytes(data)

    _, _, params = pdf_analyzer.analyze_file(p, "doc-guntha")
    assert params.get("land_area_acres") == 4.0
    assert params.get("survey_no") == "78"
