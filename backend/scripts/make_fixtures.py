"""backend/scripts/make_fixtures.py

Generate synthetic applications with clean cases and planted frauds for blind evaluation.
Uses: ReportLab + Segno + FontTools + Pillow.

Planted fraud categories:
1. expired_certificate: Fire NOC / statutory certificate expired.
2. edited_date_incremental_revision: Document date modified via appended incremental PDF updates.
3. font_mismatch: Inconsistent spliced fonts and font size discontinuities.
4. whiteout: White rectangle covering text / concealed text layer.
5. invalid_or_applicant_signature: Signed by applicant role or untrusted/tampered signature.
6. tampered_qr: Signed QR code with altered payload data.
7. duplicate_faculty_ids: Same faculty declared full-time concurrently in multiple applications.
8. reused_seal_and_lab_photo: Cross-institution reuse of lab photos and official seals.
9. geotag_outside_campus: Site inspection photo geotag located outside declared campus boundary.
10. scanned_hindi_documents: Scanned Devanagari document degraded with rotation and sensor noise.

Splits:
- dev: Random seed 42 (training / calibration split)
- blind: Random seed 1337 (held-out blind evaluation split)
"""

from __future__ import annotations

import argparse
import contextlib
import datetime
import io
import json
import random
import sys
from pathlib import Path
from typing import Any

import asn1crypto.keys as asn1_keys
import asn1crypto.x509 as asn1_x509
import imagehash
import numpy as np
import segno
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa
from cryptography.x509.oid import NameOID
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from PIL import ExifTags, Image, ImageDraw, ImageFont
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import fields, signers
from pyhanko_certvalidator.registry import SimpleCertificateStore
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from nirikshan.crypto.qr_verifier import sign_qr_payload

# ---------------------------------------------------------------------------
# 1. Custom Font Creation via FontTools
# ---------------------------------------------------------------------------

def generate_synthetic_font(output_path: Path, family_name: str = "SyntheticDevanagari") -> Path:
    """Generate a self-contained TrueType font supporting ASCII and Devanagari using fontTools."""
    fb = FontBuilder(1024, isTTF=True)
    glyph_order = [".notdef", "space"]
    glyf: dict[str, Any] = {
        ".notdef": TTGlyphPen(None).glyph(),
        "space": TTGlyphPen(None).glyph(),
    }
    cmap: dict[int, str] = {0x20: "space"}
    h_metrics: dict[str, tuple[int, int]] = {
        ".notdef": (600, 0),
        "space": (300, 0),
    }

    # Standard rectangle glyph
    pen = TTGlyphPen(None)
    pen.moveTo((50, 0))
    pen.lineTo((50, 750))
    pen.lineTo((450, 750))
    pen.lineTo((450, 0))
    pen.closePath()
    box_glyph = pen.glyph()

    # ASCII alphanumeric + common punctuation
    for cp in range(0x21, 0x7F):
        name = f"glyph_{cp:04X}"
        glyph_order.append(name)
        cmap[cp] = name
        glyf[name] = box_glyph
        h_metrics[name] = (500, 50)

    # Devanagari Unicode range U+0900 to U+097F
    for cp in range(0x0900, 0x0980):
        name = f"deva_{cp:04X}"
        glyph_order.append(name)
        cmap[cp] = name
        glyf[name] = box_glyph
        h_metrics[name] = (550, 50)

    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyf)
    fb.setupHorizontalMetrics(h_metrics)
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": family_name, "styleName": "Regular"})
    fb.setupOS2(sTypoAscender=800, sTypoDescender=-200, sTypoLineGap=0, usWinAscent=800, usWinDescent=200)
    fb.setupPost()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fb.save(str(output_path))
    return output_path


# ---------------------------------------------------------------------------
# 2. Cryptographic PKI and Keyring Generation
# ---------------------------------------------------------------------------

def setup_crypto_infrastructure(fixtures_dir: Path) -> dict[str, Any]:
    """Generate self-signed Root CA, Officer cert, Applicant cert, and Ed25519 keyring."""
    now = datetime.datetime.now(datetime.UTC)
    one_day_ago = now - datetime.timedelta(days=1)
    one_year_later = now + datetime.timedelta(days=365)

    # 1. Root CA
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "AICTE Synthetic Root CA"),
        x509.NameAttribute(NameOID.COMMON_NAME, "AICTE Scrutiny Root CA 2024"),
    ])
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(one_day_ago)
        .not_valid_after(one_year_later)
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_cert_sign=True,
                crl_sign=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(ca_key, hashes.SHA256())
    )

    ca_der = ca_cert.public_bytes(serialization.Encoding.DER)
    asn1_ca = asn1_x509.Certificate.load(ca_der)

    # Save Root CA
    ca_der_path = fixtures_dir / "trust_ca.der"
    ca_der_path.write_bytes(ca_der)
    ca_pem_path = fixtures_dir / "trust_ca.pem"
    ca_pem_path.write_bytes(ca_cert.public_bytes(serialization.Encoding.PEM))

    # Helper for leaf certificates
    def _make_leaf(cn: str, org: str, email: str = "") -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
        leaf_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        attrs = [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, org),
            x509.NameAttribute(NameOID.COMMON_NAME, cn),
        ]
        if email:
            attrs.append(x509.NameAttribute(NameOID.EMAIL_ADDRESS, email))
        leaf_name = x509.Name(attrs)
        leaf_cert = (
            x509.CertificateBuilder()
            .subject_name(leaf_name)
            .issuer_name(ca_name)
            .public_key(leaf_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(one_day_ago)
            .not_valid_after(one_year_later)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=True,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .sign(ca_key, hashes.SHA256())
        )
        return leaf_key, leaf_cert

    # 2. Officer cert (AICTE Director)
    officer_key, officer_cert = _make_leaf(
        cn="Dr. S. K. Sharma (Director)",
        org="All India Council for Technical Education",
        email="approval@aicte-india.org",
    )

    # 3. Applicant cert (Principal)
    applicant_key, applicant_cert = _make_leaf(
        cn="Principal - Apex Educational Institute",
        org="Apex Educational Trust",
        email="principal@apex-synthetic.edu.in",
    )

    # 4. Untrusted third-party cert
    untrusted_key, untrusted_cert = _make_leaf(
        cn="Unauthorized Notary Agent",
        org="Private Agent Services",
        email="agent@untrusted.org",
    )

    # 5. Ed25519 Keyring for signed QR verification
    qr_priv_key = ed25519.Ed25519PrivateKey.generate()
    qr_pub_key = qr_priv_key.public_key()
    qr_pub_pem = qr_pub_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    keyring_data = {
        "keys": [
            {
                "key_id": "aicte-ed25519-root-01",
                "algorithm": "Ed25519",
                "issuer": "All India Council for Technical Education",
                "role": "ISSUER_OFFICER",
                "public_key_pem": qr_pub_pem,
            }
        ]
    }
    keyring_path = fixtures_dir / "keyring.json"
    keyring_path.write_text(json.dumps(keyring_data, indent=2), encoding="utf-8")

    return {
        "ca_cert": ca_cert,
        "ca_der": ca_der,
        "asn1_ca": asn1_ca,
        "officer": (officer_key, officer_cert),
        "applicant": (applicant_key, applicant_cert),
        "untrusted": (untrusted_key, untrusted_cert),
        "qr_priv_key": qr_priv_key,
        "qr_key_id": "aicte-ed25519-root-01",
        "keyring_path": keyring_path,
    }


# ---------------------------------------------------------------------------
# 3. PDF and Image Document Creators
# ---------------------------------------------------------------------------

def make_clean_document(
    dest_path: Path,
    title: str,
    institution: str,
    app_no: str,
    lines: list[str],
) -> None:
    """Generate a clean, single-revision PDF document using ReportLab."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(dest_path), pagesize=A4)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 800, title)
    c.setFont("Helvetica", 10)
    c.drawString(72, 780, f"Institution: {institution} | Application No: {app_no}")
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.line(72, 770, 523, 770)

    y = 740
    c.setFont("Helvetica", 11)
    for line in lines:
        c.drawString(72, y, line)
        y -= 25

    c.setFont("Helvetica-Oblique", 9)
    c.drawString(72, 100, "Official AICTE Regulatory Scrutiny Copy — Confidential")
    c.showPage()
    c.save()


def make_expired_cert_document(
    dest_path: Path,
    institution: str,
    app_no: str,
) -> None:
    """Generate an expired Fire Safety NOC certificate."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(dest_path), pagesize=A4)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 800, "FIRE & RESCUE SERVICES DEPARTMENT — FIRE SAFETY NOC")
    c.setFont("Helvetica", 10)
    c.drawString(72, 780, f"Institution: {institution} | Ref: {app_no}")
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.line(72, 770, 523, 770)

    c.setFont("Helvetica", 11)
    c.drawString(72, 740, "Certificate Number: NOC/FIRE/2021/8812")
    c.drawString(72, 715, "Status: EXPIRED on 2022-12-31")
    c.drawString(72, 690, "Deficiency: Renewal application pending re-inspection.")
    c.drawString(72, 665, "Validity: 2021-01-01 to 2022-12-31 (EXPIRED)")

    c.showPage()
    c.save()


def make_incremental_revision_document(
    dest_path: Path,
    institution: str,
    app_no: str,
) -> None:
    """Generate a PDF containing multiple appended incremental updates / revisions."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 800, "LAND USE CONVERSION ORDER — STATE REVENUE DEPT")
    c.setFont("Helvetica", 10)
    c.drawString(72, 780, f"Institution: {institution} | Application No: {app_no}")
    c.setFont("Helvetica", 11)
    c.drawString(72, 740, "Order No: REV/CONV/2023/108")
    c.drawString(72, 715, "Original Sanction Date: 2023-01-10")
    c.drawString(72, 690, "Permitted Extent: 2.50 Acres (Survey No. 44/1)")
    c.showPage()
    c.save()

    raw = buf.getvalue()
    # Inject 5 incremental revisions (%%EOF markers) and JavaScript tampering marker
    tampered = raw + b"\n%%EOF\n%%EOF\n%%EOF\n%%EOF\n%%EOF\n/JavaScript (app.alert('Tampered'));\n"
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_bytes(tampered)


def make_font_mismatch_document(
    dest_path: Path,
    institution: str,
    app_no: str,
    custom_font_name: str,
) -> None:
    """Generate a document with excessive font diversity and font size discontinuities."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(dest_path), pagesize=A4)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 800, "REGISTERED SALE INDENTURE — LAND TITLE")
    c.setFont("Helvetica", 10)
    c.drawString(72, 780, f"Institution: {institution} | Application No: {app_no}")

    # Use 5+ distinct font families on the same page
    fonts_and_sizes = [
        ("Helvetica", 10, "Paragraph 1: Clear and marketable title confirmed by vendor."),
        ("Times-Roman", 12, "Paragraph 2: Encumbrance certificate verified for past 30 years."),
        ("Courier", 9, "Paragraph 3: Land situated in Survey No. 129/A with boundary demarcations."),
        ("Helvetica-Bold", 11, "Paragraph 4: Property converted for technical college use."),
        (custom_font_name, 10, "Paragraph 5: Spliced clause inserted from foreign template."),
        ("Times-Bold", 42, "DISCONTINUOUS LARGE HEADER (RATIO > 4X)"),
    ]

    y = 740
    for font, size, text in fonts_and_sizes:
        c.setFont(font, size)
        c.drawString(72, y, text)
        y -= 45

    c.showPage()
    c.save()


def make_whiteout_document(
    dest_path: Path,
    institution: str,
    app_no: str,
) -> None:
    """Generate a PDF containing solid white rectangle concealing critical text."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(dest_path), pagesize=A4)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 800, "TOWN & COUNTRY PLANNING APPROVED BUILDING SANCTION")
    c.setFont("Helvetica", 10)
    c.drawString(72, 780, f"Institution: {institution} | Application No: {app_no}")

    c.setFont("Helvetica", 11)
    c.drawString(72, 740, "Sanctioned Built-Up Area: 12,500 sq.m")
    c.drawString(72, 715, "Structural Stability Certificate: Approved unconditionally")

    # Original text that is visually whited out
    c.drawString(72, 680, "Deficiency Clause: Structural sanction revoked due to setback violations")

    # Draw solid white rectangle concealing the deficiency clause
    c.setFillColorRGB(1.0, 1.0, 1.0)
    c.rect(70, 672, 450, 24, fill=1, stroke=0)

    # Overwrite replacement text on top
    c.setFillColorRGB(0.0, 0.0, 0.0)
    c.setFont("Helvetica", 10)
    c.drawString(72, 680, "Compliance Clause: All setback norms fully verified and in order.")

    c.showPage()
    c.save()


def make_signed_pdf_document(
    dest_path: Path,
    institution: str,
    app_no: str,
    signer_key: rsa.RSAPrivateKey,
    signer_cert: x509.Certificate,
    root_ca: asn1_x509.Certificate,
    tamper_bytes: bool = False,
) -> None:
    """Generate a cryptographically signed PDF using pyHanko."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 800, "AICTE FORMAL REGULATORY APPROVAL ORDER")
    c.setFont("Helvetica", 10)
    c.drawString(72, 780, f"Institution: {institution} | Application: {app_no}")
    c.setFont("Helvetica", 11)
    c.drawString(72, 740, "Approval is hereby accorded under AICTE Act for Academic Year 2024-2025.")
    c.drawString(72, 715, "This document bears a verifiable cryptographic PDF digital signature.")
    c.showPage()
    c.save()
    buf.seek(0)

    asn1_leaf_cert = asn1_x509.Certificate.load(signer_cert.public_bytes(serialization.Encoding.DER))
    asn1_leaf_key = asn1_keys.PrivateKeyInfo.load(
        signer_key.private_bytes(
            serialization.Encoding.DER,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    store = SimpleCertificateStore.from_certs([root_ca])
    signer = signers.SimpleSigner(signing_cert=asn1_leaf_cert, signing_key=asn1_leaf_key, cert_registry=store)

    w = IncrementalPdfFileWriter(buf)
    fields.append_signature_field(w, sig_field_spec=fields.SigFieldSpec(sig_field_name="AICTE_Signature"))
    out = io.BytesIO()
    signers.sign_pdf(w, signers.PdfSignatureMetadata(field_name="AICTE_Signature"), signer=signer, output=out)
    signed_bytes = out.getvalue()

    if tamper_bytes:
        # Corrupt the signed byte range
        signed_bytes = signed_bytes + b"\n%%EOF\n%TAMPERED_BYTE_PAYLOAD_VIOLATION\n"

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_bytes(signed_bytes)


def make_signed_qr_code(
    dest_path: Path,
    data: dict[str, Any],
    priv_key: ed25519.Ed25519PrivateKey,
    key_id: str,
    tamper: bool = False,
) -> None:
    """Generate a signed QR code PNG using Segno."""
    payload = sign_qr_payload(data, priv_key, key_id=key_id)
    if tamper:
        # Alter the data payload without updating the signature
        payload["data"]["tampered_flag"] = True
        payload["data"]["land_area_acres"] = 999.0

    qr = segno.make(json.dumps(payload))
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    qr.save(str(dest_path), kind="png", scale=5)


def make_synthetic_photo(
    dest_path: Path,
    title: str,
    lat: float,
    lon: float,
    seed_offset: int = 0,
    style: str = "computer_lab",
) -> str:
    """Generate a synthetic site/lab inspection photo with EXIF GPS coordinates."""
    if style == "chemistry_lab":
        bg_color = (245, 240, 220)
        img = Image.new("RGB", (640, 480), color=bg_color)
        draw = ImageDraw.Draw(img)
        # Wooden benches and round flasks
        draw.rectangle([30, 280, 610, 450], fill=(160, 110, 60), outline=(100, 70, 30), width=3)
        for x in (80, 220, 360, 500):
            draw.ellipse([x, 190, x + 70, 280], fill=(255, 140, 0), outline=(180, 80, 0), width=2)
            draw.rectangle([x + 25, 150, x + 45, 190], fill=(200, 240, 255), outline=(100, 150, 180), width=2)
    elif style == "physics_lab":
        bg_color = (25, 30, 45)
        img = Image.new("RGB", (640, 480), color=bg_color)
        draw = ImageDraw.Draw(img)
        # Dark optical table with laser beams
        draw.rectangle([50, 260, 590, 440], fill=(60, 70, 85), outline=(120, 140, 160), width=2)
        draw.line([60, 310, 580, 310], fill=(255, 20, 20), width=4)
        draw.line([300, 200, 300, 420], fill=(20, 255, 50), width=3)
        for x in (120, 260, 400, 520):
            draw.rectangle([x, 280, x + 40, 340], fill=(180, 190, 200), outline=(220, 230, 240), width=2)
    elif style == "library":
        bg_color = (70, 45, 30)
        img = Image.new("RGB", (640, 480), color=bg_color)
        draw = ImageDraw.Draw(img)
        # Vertical bookshelves
        for x in range(30, 610, 35):
            book_col = (180, 50, 40) if x % 70 == 0 else (210, 190, 90) if x % 35 == 0 else (50, 120, 70)
            draw.rectangle([x, 60, x + 25, 420], fill=book_col, outline=(30, 20, 10), width=1)
    else:  # default computer_lab
        bg_color = (220, 230, 245)
        img = Image.new("RGB", (640, 480), color=bg_color)
        draw = ImageDraw.Draw(img)
        # Rows of modern computer monitors
        draw.rectangle([40, 290, 600, 440], fill=(130, 140, 155), outline=(80, 90, 100), width=2)
        for x in (70, 190, 310, 430):
            draw.rectangle([x, 180, x + 90, 260], fill=(10, 15, 25), outline=(120, 180, 240), width=3)
            draw.rectangle([x + 10, 190, x + 80, 250], fill=(0, 160, 255))
            draw.rectangle([x + 35, 260, x + 55, 290], fill=(80, 90, 100))

    # Add text banner
    draw.text((50, 25), f"AICTE Lab Scrutiny: {title}", fill=(20, 30, 40) if bg_color[0] > 100 else (240, 240, 240))
    draw.text((50, 45), f"GPS Target: ({lat:.4f}, {lon:.4f})", fill=(60, 70, 80) if bg_color[0] > 100 else (200, 210, 220))

    # Add EXIF with GPS
    exif = img.getexif()
    exif[ExifTags.Base.Make] = "Nirikshan Camera"
    exif[ExifTags.Base.Model] = "Field-Inspector-Pro"
    exif[ExifTags.Base.DateTimeOriginal] = "2024:05:15 11:30:00"
    exif[ExifTags.Base.DateTime] = "2024:05:15 11:30:00"

    gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
    lat_deg = int(abs(lat))
    lat_min = int((abs(lat) - lat_deg) * 60)
    lat_sec = round(((abs(lat) - lat_deg) * 60 - lat_min) * 60, 2)

    lon_deg = int(abs(lon))
    lon_min = int((abs(lon) - lon_deg) * 60)
    lon_sec = round(((abs(lon) - lon_deg) * 60 - lon_min) * 60, 2)

    gps_ifd[ExifTags.GPS.GPSLatitude] = (lat_deg, lat_min, lat_sec)
    gps_ifd[ExifTags.GPS.GPSLatitudeRef] = "N" if lat >= 0 else "S"
    gps_ifd[ExifTags.GPS.GPSLongitude] = (lon_deg, lon_min, lon_sec)
    gps_ifd[ExifTags.GPS.GPSLongitudeRef] = "E" if lon >= 0 else "W"

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest_path, format="JPEG", exif=exif)

    return str(imagehash.phash(img))


def make_circular_seal(
    dest_path: Path,
    authority_name: str,
    place_name: str,
    seal_type: str = "circle",
) -> str:
    """Generate a synthetic official seal and return its pHash."""
    img = Image.new("RGBA", (300, 300), color=(255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    if seal_type == "fire_service":
        seal_color = (180, 30, 30, 230)  # Reddish
        draw.ellipse([20, 20, 280, 280], outline=seal_color, width=5)
        draw.ellipse([45, 45, 255, 255], outline=seal_color, width=2)
        # Cross motif
        draw.line([150, 60, 150, 240], fill=seal_color, width=3)
        draw.line([60, 150, 240, 150], fill=seal_color, width=3)
    elif seal_type == "municipal":
        seal_color = (20, 120, 40, 230)  # Greenish
        draw.rectangle([30, 30, 270, 270], outline=seal_color, width=4)
        draw.rectangle([50, 50, 250, 250], outline=seal_color, width=2)
    elif seal_type == "registrar":
        seal_color = (90, 20, 140, 230)  # Purple
        draw.polygon([(150, 20), (280, 150), (150, 280), (20, 150)], outline=seal_color, width=4)
    else:  # default revenue circle
        seal_color = (20, 60, 160, 230)
        draw.ellipse([20, 20, 280, 280], outline=seal_color, width=4)
        draw.ellipse([35, 35, 265, 265], outline=seal_color, width=2)
        draw.ellipse([70, 70, 230, 230], outline=seal_color, width=2)

    draw.text((45, 115), authority_name[:22].upper(), fill=seal_color)
    draw.text((70, 140), place_name.upper(), fill=seal_color)
    draw.text((80, 165), "GOVERNMENT OF INDIA", fill=seal_color)

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest_path, format="PNG")
    return str(imagehash.phash(img.convert("RGB")))


def make_degraded_scanned_hindi_doc(
    dest_path: Path,
    institution: str,
    font_path: Path,
) -> None:
    """Generate a scanned Hindi document with Devanagari font, degraded with rotation and noise."""
    img = Image.new("L", (850, 1200), color=252)
    draw = ImageDraw.Draw(img)

    # Load font
    try:
        font = ImageFont.truetype(str(font_path), 22)
        font_sm = ImageFont.truetype(str(font_path), 18)
    except Exception:
        font = ImageFont.load_default()
        font_sm = font

    # Draw Hindi regulatory text
    draw.text((60, 60), "राज्य राजस्व विभाग — खतौनी एवं भूमि रूपांतरण आदेश", font=font, fill=30)
    draw.text((60, 100), f"संस्थान का नाम: {institution}", font=font_sm, fill=50)
    draw.text((60, 140), "भूमि का कुल क्षेत्रफल (एकड़): 4.50 एकड़", font=font_sm, fill=50)
    draw.text((60, 180), "सर्वे संख्या / खसरा नंबर: 124/2A", font=font_sm, fill=50)
    draw.text((60, 220), "अग्निशमन अनापत्ति प्रमाण पत्र वैध: हाँ (सत्यापित)", font=font_sm, fill=50)
    draw.text((60, 260), "तहसीलदार एवं सक्षम प्राधिकारी हस्ताक्षर", font=font_sm, fill=50)

    # Border simulating official letterhead
    draw.rectangle([40, 40, 810, 1160], outline=120, width=2)

    # 1. Rotate by realistic scanner skew (1.5 degrees)
    img = img.rotate(1.5, resample=Image.BICUBIC, fillcolor=252)

    # 2. Add sensor noise (Gaussian noise + salt/pepper dust)
    arr = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, 7.0, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)

    # Dust particles
    dust = np.random.rand(*arr.shape) < 0.001
    arr[dust] = 40
    degraded_img = Image.fromarray(arr)

    # Save as image-only PDF (no native text layer)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    degraded_img.save(dest_path, "PDF")


# ---------------------------------------------------------------------------
# 4. Master Synthetic Fixture Generator
# ---------------------------------------------------------------------------

def generate_fixtures(
    output_dir: Path,
    num_apps: int = 24,
    seed_dev: int = 42,
    seed_blind: int = 1337,
) -> dict[str, Any]:
    """Generate synthetic application dossiers partitioned into dev and blind splits."""
    output_dir.mkdir(parents=True, exist_ok=True)
    fonts_dir = output_dir / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)

    # Generate custom font with fontTools
    custom_font_path = fonts_dir / "SyntheticMismatchFont.ttf"
    generate_synthetic_font(custom_font_path, family_name="SyntheticMismatchFont")
    pdfmetrics.registerFont(TTFont("SyntheticMismatchFont", str(custom_font_path)))

    # Setup PKI infrastructure
    crypto_infra = setup_crypto_infrastructure(output_dir)

    manifest: dict[str, Any] = {
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "total_applications": num_apps,
        "splits": {
            "dev": {"seed": seed_dev, "applications": []},
            "blind": {"seed": seed_blind, "applications": []},
        },
        "applications": {},
    }

    # Half dev, half blind
    num_per_split = num_apps // 2
    splits = [
        ("dev", seed_dev, num_per_split),
        ("blind", seed_blind, num_apps - num_per_split),
    ]

    for split_name, seed, count in splits:
        random.seed(seed)
        np.random.seed(seed)

        split_dir = output_dir / split_name
        split_dir.mkdir(parents=True, exist_ok=True)

        # Reusable shared assets for cross-app tests in this split
        shared_fac_aadhaar = f"{random.randint(1000, 9999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}"
        shared_lab_photo_path = split_dir / "shared_assets" / "shared_physics_lab.jpg"
        shared_photo_phash = make_synthetic_photo(
            shared_lab_photo_path,
            "Physics Optical Apparatus",
            28.6139,
            77.2090,
            seed_offset=1,
            style="physics_lab",
        )
        shared_seal_path = split_dir / "shared_assets" / "shared_circular_seal.png"
        shared_seal_phash = make_circular_seal(
            shared_seal_path, "Delhi State Revenue Dept", "Delhi", seal_type="registrar"
        )

        # Define 12 standard applications in the split
        for idx in range(1, count + 1):
            app_id = f"app_{split_name}_{idx:02d}"
            app_dir = split_dir / app_id
            docs_dir = app_dir / "documents"
            photos_dir = app_dir / "photos"
            docs_dir.mkdir(parents=True, exist_ok=True)
            photos_dir.mkdir(parents=True, exist_ok=True)

            inst_name = f"Institution {split_name.title()} #{idx}"
            app_no = f"AICTE/2024/{split_name.upper()}/{idx:03d}"

            # Declared campus polygon (New Delhi coordinates approx 28.61 to 28.62)
            campus_poly = [
                (77.2000, 28.6100),
                (77.2200, 28.6100),
                (77.2200, 28.6250),
                (77.2000, 28.6250),
            ]

            planted: list[str] = []
            is_clean = False
            extracted_params: dict[str, Any] = {
                "land_area_acres": 4.5,
                "is_contiguous": True,
                "survey_no_deed": "104/1A",
                "survey_no_conversion": "104/1A",
                "survey_no_building_plan": "104/1A",
                "built_up_area_sqm": 12500.0,
                "fire_noc_expired": False,
                "faculty_count": 60,
                "cadre_professors": 6,
                "cadre_assoc_professors": 14,
                "cadre_asst_professors": 40,
                "fdr_amount_lakhs": 100.0,
                "faculty": [],
                "photos": [],
                "seals": [],
            }

            # Map index to application scenario
            scenario_idx = ((idx - 1) % 12) + 1

            if scenario_idx in (1, 2):
                # Clean Control Application
                is_clean = True
                make_clean_document(
                    docs_dir / "land_deed.pdf",
                    "REGISTERED LAND SALE DEED",
                    inst_name,
                    app_no,
                    ["Freehold clear title of 4.50 acres verified.", "Survey Number: 104/1A."],
                )
                make_clean_document(
                    docs_dir / "fire_noc.pdf",
                    "FIRE SAFETY CLEARANCE CERTIFICATE",
                    inst_name,
                    app_no,
                    ["Fire fighting system fully operational.", "Certificate valid through 2026-12-31."],
                )
                # Officer signed PDF
                make_signed_pdf_document(
                    docs_dir / "approval_letter.pdf",
                    inst_name,
                    app_no,
                    signer_key=crypto_infra["officer"][0],
                    signer_cert=crypto_infra["officer"][1],
                    root_ca=crypto_infra["asn1_ca"],
                )
                # Valid signed QR
                make_signed_qr_code(
                    photos_dir / "approval_qr.png",
                    {"institution": inst_name, "app_no": app_no, "land_acres": 4.5},
                    priv_key=crypto_infra["qr_priv_key"],
                    key_id=crypto_infra["qr_key_id"],
                )
                # Photo inside campus with distinct style per application
                photo_style = "computer_lab" if scenario_idx == 1 else "chemistry_lab"
                seal_type = "fire_service" if scenario_idx == 1 else "municipal"
                authority = "Delhi Fire Service" if scenario_idx == 1 else "Municipal Corporation"

                p_hash = make_synthetic_photo(
                    photos_dir / "lab_view.jpg",
                    f"{photo_style.replace('_', ' ').title()}",
                    28.6145,
                    77.2085,
                    seed_offset=idx,
                    style=photo_style,
                )
                s_hash = make_circular_seal(photos_dir / "seal.png", authority, "Delhi", seal_type=seal_type)
                extracted_params["photos"].append({"phash": p_hash, "type": photo_style.upper()})
                extracted_params["seals"].append({"phash": s_hash, "issuing_authority": authority})
                extracted_params["faculty"].append({
                    "aadhaar": f"{random.randint(1000, 9999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}",
                    "name": f"Dr. Sunil Kumar #{idx}",
                    "employment_type": "FULL_TIME",
                    "periods": ["2024-2025"],
                })

            elif scenario_idx == 3:
                # 1. Expired Certificate
                planted.append("expired_certificate")
                extracted_params["fire_noc_expired"] = True
                make_expired_cert_document(docs_dir / "fire_safety_noc.pdf", inst_name, app_no)

            elif scenario_idx == 4:
                # 2. Edited Date via Incremental Revision
                planted.append("edited_date_incremental_revision")
                make_incremental_revision_document(docs_dir / "land_conversion_order.pdf", inst_name, app_no)

            elif scenario_idx == 5:
                # 3. Font Mismatch
                planted.append("font_mismatch")
                make_font_mismatch_document(docs_dir / "land_deed.pdf", inst_name, app_no, "SyntheticMismatchFont")

            elif scenario_idx == 6:
                # 4. Whiteout
                planted.append("whiteout")
                make_whiteout_document(docs_dir / "building_sanction.pdf", inst_name, app_no)

            elif scenario_idx == 7:
                # 5. Invalid / Applicant Signature
                planted.append("invalid_or_applicant_signature")
                make_signed_pdf_document(
                    docs_dir / "official_sanction.pdf",
                    inst_name,
                    app_no,
                    signer_key=crypto_infra["applicant"][0],
                    signer_cert=crypto_infra["applicant"][1],
                    root_ca=crypto_infra["asn1_ca"],
                )

            elif scenario_idx == 8:
                # 6. Tampered QR
                planted.append("tampered_qr")
                make_signed_qr_code(
                    photos_dir / "verification_qr.png",
                    {"institution": inst_name, "app_no": app_no, "land_acres": 4.5},
                    priv_key=crypto_infra["qr_priv_key"],
                    key_id=crypto_infra["qr_key_id"],
                    tamper=True,
                )

            elif scenario_idx == 9:
                # 7. Duplicate Faculty IDs & Shared Photo/Seal (Paired with app 10)
                planted.extend(["duplicate_faculty_ids", "reused_seal_and_lab_photo"])
                extracted_params["faculty"].append({
                    "aadhaar": shared_fac_aadhaar,
                    "name": "Dr. Ramesh Sharma (Shared)",
                    "employment_type": "FULL_TIME",
                    "periods": ["2024-2025"],
                    "designation": "Professor & HOD",
                })
                # Shared lab photo and seal with App 10
                extracted_params["photos"].append({
                    "phash": shared_photo_phash,
                    "type": "PHYSICS_LAB",
                    "source_path": str(shared_lab_photo_path),
                })
                extracted_params["seals"].append({
                    "phash": shared_seal_phash,
                    "issuing_authority": "Delhi State Revenue Dept",
                    "source_path": str(shared_seal_path),
                })

            elif scenario_idx == 10:
                # 8. Reused Seal and Lab Photo (Shares with app 9 + shared faculty)
                planted.extend(["reused_seal_and_lab_photo", "duplicate_faculty_ids"])
                extracted_params["faculty"].append({
                    "aadhaar": shared_fac_aadhaar,
                    "name": "Dr. Ramesh Sharma (Shared)",
                    "employment_type": "FULL_TIME",
                    "periods": ["2024-2025"],
                    "designation": "Professor",
                })
                # Reused lab photo
                extracted_params["photos"].append({
                    "phash": shared_photo_phash,
                    "type": "PHYSICS_LAB",
                    "source_path": str(shared_lab_photo_path),
                })
                # Reused seal under different issuing authority
                extracted_params["seals"].append({
                    "phash": shared_seal_phash,
                    "issuing_authority": "Pune Municipal Corporation",
                    "source_path": str(shared_seal_path),
                })

            elif scenario_idx == 11:
                # 9. Geotag Outside Campus
                planted.append("geotag_outside_campus")
                # Photo taken 55 km away outside campus polygon
                make_synthetic_photo(photos_dir / "site_photo.jpg", "Campus Exterior", 28.1500, 76.8000)

            elif scenario_idx == 12:
                # 10. Scanned Hindi Document
                planted.append("scanned_hindi_documents")
                make_degraded_scanned_hindi_doc(
                    docs_dir / "khatauni_revenue_hi.pdf",
                    inst_name,
                    font_path=custom_font_path,
                )

            # Save application metadata
            app_meta = {
                "application_id": app_id,
                "split": split_name,
                "institution_name": inst_name,
                "application_number": app_no,
                "is_clean": is_clean,
                "planted_frauds": planted,
                "campus_polygon": campus_poly,
                "extracted_params": extracted_params,
                "files": {
                    "documents": [str(p.relative_to(output_dir)) for p in docs_dir.glob("*")],
                    "photos": [str(p.relative_to(output_dir)) for p in photos_dir.glob("*")],
                },
            }
            (app_dir / "meta.json").write_text(json.dumps(app_meta, indent=2), encoding="utf-8")

            manifest["splits"][split_name]["applications"].append(app_id)
            manifest["applications"][app_id] = app_meta

    # Save master ground truth manifest
    manifest_path = output_dir / "ground_truth.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic Nirikshan test applications and ground truth manifest.")
    parser.add_argument("--num-apps", type=int, default=24, help="Total number of applications to generate (default: 24).")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent.parent / "tests" / "fixtures" / "synthetic", help="Output directory.")
    parser.add_argument("--seed-dev", type=int, default=42, help="Seed for dev split (default: 42).")
    parser.add_argument("--seed-blind", type=int, default=1337, help="Seed for blind split (default: 1337).")

    args = parser.parse_args()

    print(f"Generating {args.num_apps} synthetic applications in: {args.output_dir}")
    manifest = generate_fixtures(
        output_dir=args.output_dir,
        num_apps=args.num_apps,
        seed_dev=args.seed_dev,
        seed_blind=args.seed_blind,
    )
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        with contextlib.suppress(Exception):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print(f"[OK] Generated {len(manifest['applications'])} applications successfully.")
    print(f"     Manifest: {args.output_dir / 'ground_truth.json'}")


if __name__ == "__main__":
    main()
