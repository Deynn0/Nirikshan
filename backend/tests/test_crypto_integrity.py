"""Comprehensive test suite for cryptographic and physical integrity verification.

Tests:
1. Self-made test CA generation with cryptography.
2. Sign fixture PDFs with pyHanko:
   - Issuer officer signed with trusted root chain -> CRYPTOGRAPHIC trust.
   - Applicant signed document -> APPLICANT role, UNVERIFIED_CLAIM trust (never CRYPTOGRAPHIC).
   - Unknown third-party signer -> UNKNOWN role, STRUCTURAL_FORENSIC trust.
   - Post-signature byte tampering -> is_tampered=True, STRUCTURAL_FORENSIC.
3. Signed QR verification:
   - Ed25519 sign, QR encode, decode, verify roundtrip -> VALID.
   - ECDSA sign, QR encode, decode, verify roundtrip -> VALID.
   - Tampered data payload -> INVALID.
   - Unregistered key_id -> UNKNOWN_ISSUER.
4. Photo integrity:
   - EXIF extraction (camera device, timestamp, GPS DMS conversion).
   - Shapely geofence inside/outside campus polygon.
   - Metadata stripping and editing software anomaly detection.
   - C2PA manifest validation graceful handling.
5. FastAPI /scan endpoint:
   - GET /scan mobile HTML with camera input.
   - POST /scan verification returning VALID/INVALID/UNKNOWN_ISSUER.
"""

from __future__ import annotations

import datetime
import io
import json

import asn1crypto.keys as asn1_keys
import asn1crypto.x509 as asn1_x509
import pytest
import qrcode
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa
from cryptography.x509.oid import NameOID
from httpx import ASGITransport, AsyncClient
from PIL import ExifTags, Image
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import fields, signers
from pyhanko_certvalidator.registry import SimpleCertificateStore
from reportlab.pdfgen import canvas
from shapely.geometry import Polygon

from nirikshan.crypto.pdf_verifier import (
    verify_pdf_signatures,
)
from nirikshan.crypto.photo_integrity import (
    validate_c2pa,
    verify_photo_integrity,
)
from nirikshan.crypto.qr_verifier import (
    Keyring,
    KeyringEntry,
    QRVerificationStatus,
    decode_qr_from_image,
    sign_qr_payload,
    verify_qr_payload,
)
from nirikshan.crypto.signer_disambiguation import (
    ApplicantIdentity,
    IssuerRegistry,
    SignerRole,
    disambiguate_signer,
)
from nirikshan.main import app
from nirikshan.trust.ladder import TrustLevel

# ---------------------------------------------------------------------------
# Test CA and Certificate Generator Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_pki():
    """Create in-memory self-made Root CA and subordinate certificates."""
    now = datetime.datetime.now(datetime.UTC)
    one_day_ago = now - datetime.timedelta(days=1)
    one_year_later = now + datetime.timedelta(days=365)

    # 1. Root CA
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Root Certifying Authority"),
        x509.NameAttribute(NameOID.COMMON_NAME, "Test RCAI 2024"),
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
                    content_commitment=True,  # non-repudiation
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

    # 2. Issuer Officer Certificate (AICTE)
    officer_key, officer_cert = _make_leaf(
        cn="Dr. S. K. Sharma (Director)",
        org="All India Council for Technical Education",
        email="approval@aicte-india.org",
    )

    # 3. Applicant Certificate (Apex Engineering Institute)
    applicant_key, applicant_cert = _make_leaf(
        cn="Principal - Apex Engineering Institute",
        org="Apex Education Trust",
        email="principal@apex-engineering.edu.in",
    )

    # 4. Unknown Third-Party Certificate
    unknown_key, unknown_cert = _make_leaf(
        cn="John Doe",
        org="Independent Notary Services Ltd",
        email="john@notary.example",
    )

    # Convert CA to asn1crypto format for pyHanko
    asn1_ca = asn1_x509.Certificate.load(ca_cert.public_bytes(serialization.Encoding.DER))

    return {
        "ca_cert": ca_cert,
        "ca_key": ca_key,
        "asn1_ca": asn1_ca,
        "officer": (officer_key, officer_cert),
        "applicant": (applicant_key, applicant_cert),
        "unknown": (unknown_key, unknown_cert),
    }


def _create_signed_pdf(key: rsa.RSAPrivateKey, cert: x509.Certificate, root_ca: asn1_x509.Certificate) -> bytes:
    """Helper to generate a cleanly signed PDF using pyHanko."""
    # 1. Base PDF
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pageCompression=0)
    c.drawString(72, 750, "Regulatory Approval NOC Document")
    c.drawString(72, 720, "This document certifies regulatory compliance.")
    c.save()
    buf.seek(0)

    # 2. Setup pyHanko SimpleSigner
    asn1_leaf_cert = asn1_x509.Certificate.load(cert.public_bytes(serialization.Encoding.DER))
    asn1_leaf_key = asn1_keys.PrivateKeyInfo.load(
        key.private_bytes(serialization.Encoding.DER, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    )
    store = SimpleCertificateStore.from_certs([root_ca])
    signer = signers.SimpleSigner(signing_cert=asn1_leaf_cert, signing_key=asn1_leaf_key, cert_registry=store)

    # 3. Sign
    w = IncrementalPdfFileWriter(buf)
    fields.append_signature_field(w, sig_field_spec=fields.SigFieldSpec(sig_field_name="RegulatorySign"))
    out = io.BytesIO()
    signers.sign_pdf(w, signers.PdfSignatureMetadata(field_name="RegulatorySign"), signer=signer, output=out)
    return out.getvalue()


# ---------------------------------------------------------------------------
# Deliverable 1 & 2: PDF Signatures & Signer Disambiguation Tests
# ---------------------------------------------------------------------------

def test_pdf_signature_verification_issuer_officer(test_pki):
    """Test valid signature by authorized ISSUER_OFFICER achieves CRYPTOGRAPHIC trust."""
    officer_key, officer_cert = test_pki["officer"]
    signed_pdf = _create_signed_pdf(officer_key, officer_cert, test_pki["asn1_ca"])

    applicant = ApplicantIdentity(
        institution_name="Apex Engineering Institute",
        applicant_name="Principal Apex",
    )

    report = verify_pdf_signatures(
        signed_pdf,
        trust_roots=[test_pki["asn1_ca"]],
        applicant=applicant,
        source_document_name="AICTE_Approval_Letter.pdf",
    )

    assert report.has_signatures is True
    assert report.signature_count == 1
    assert report.is_overall_tampered is False

    sig = report.signatures[0]
    assert sig.is_intact is True
    assert sig.is_valid is True
    assert sig.is_trusted is True
    assert sig.coverage_level == "ENTIRE_FILE"
    assert sig.signer_role == SignerRole.ISSUER_OFFICER
    assert sig.assessed_trust_level == TrustLevel.CRYPTOGRAPHIC

    # EvidenceItem checks
    ev = sig.evidence_item
    assert ev is not None
    assert ev.effective_trust_level() == TrustLevel.CRYPTOGRAPHIC
    assert ev.is_self_attested is False
    assert ev.is_tampered is False
    assert ev.trust_rank == 60


def test_pdf_signature_verification_applicant_cannot_reach_cryptographic(test_pki):
    """An applicant-signed document must never reach Cryptographic-level trust as issuer proof."""
    app_key, app_cert = test_pki["applicant"]
    signed_pdf = _create_signed_pdf(app_key, app_cert, test_pki["asn1_ca"])

    applicant = ApplicantIdentity(
        institution_name="Apex Engineering Institute",
        trust_or_society_name="Apex Education Trust",
    )

    report = verify_pdf_signatures(
        signed_pdf,
        trust_roots=[test_pki["asn1_ca"]],
        applicant=applicant,
        source_document_name="Applicant_Declaration.pdf",
    )

    assert report.has_signatures is True
    sig = report.signatures[0]

    # Must be classified as APPLICANT
    assert sig.signer_role == SignerRole.APPLICANT
    assert sig.assessed_trust_level == TrustLevel.UNVERIFIED_CLAIM

    # Non-negotiable: Effective trust level is UNVERIFIED_CLAIM (Rank 0)
    ev = sig.evidence_item
    assert ev is not None
    assert ev.is_self_attested is True
    assert ev.effective_trust_level() == TrustLevel.UNVERIFIED_CLAIM
    assert ev.trust_rank == 0


def test_pdf_signature_verification_unknown_signer(test_pki):
    """Test signature from an unknown entity is classified as UNKNOWN."""
    unk_key, unk_cert = test_pki["unknown"]
    signed_pdf = _create_signed_pdf(unk_key, unk_cert, test_pki["asn1_ca"])

    applicant = ApplicantIdentity(
        institution_name="Apex Engineering Institute",
    )

    report = verify_pdf_signatures(
        signed_pdf,
        trust_roots=[test_pki["asn1_ca"]],
        applicant=applicant,
        source_document_name="Unknown_NOC.pdf",
    )

    assert report.has_signatures is True
    sig = report.signatures[0]
    assert sig.signer_role == SignerRole.UNKNOWN
    # Cannot reach CRYPTOGRAPHIC or ISSUER trust level
    assert sig.assessed_trust_level in (TrustLevel.STRUCTURAL_FORENSIC, TrustLevel.UNVERIFIED_CLAIM)


def test_pdf_signature_tampering_detection(test_pki):
    """Tampering with bytes after signing must be detected (is_tampered=True)."""
    officer_key, officer_cert = test_pki["officer"]
    signed_pdf = _create_signed_pdf(officer_key, officer_cert, test_pki["asn1_ca"])

    # Tamper with byte content inside the PDF
    tampered_bytes = bytearray(signed_pdf)
    # Target some visible text in stream
    idx = tampered_bytes.find(b"Regulatory Approval")
    if idx != -1:
        tampered_bytes[idx:idx + 10] = b"FAKED_TEXT"
    else:
        # Flip bytes in the middle of document
        tampered_bytes[len(tampered_bytes) // 2] ^= 0xFF

    report = verify_pdf_signatures(
        bytes(tampered_bytes),
        trust_roots=[test_pki["asn1_ca"]],
        source_document_name="Tampered_NOC.pdf",
    )

    assert report.is_overall_tampered is True
    sig = report.signatures[0]
    assert sig.is_tampered is True
    assert sig.is_intact is False
    assert sig.assessed_trust_level == TrustLevel.STRUCTURAL_FORENSIC
    assert sig.evidence_item.effective_trust_level() == TrustLevel.STRUCTURAL_FORENSIC


def test_signer_disambiguation_rules():
    """Unit tests for disambiguate_signer matching edge cases."""
    applicant = ApplicantIdentity(
        institution_name="National Institute of Technology Karnataka",
        applicant_name="Prof. Rao",
        email="director@nitk.edu.in",
    )
    reg = IssuerRegistry()

    # 1. Matching applicant
    res_app = disambiguate_signer(
        {"CN": "Prof. Rao", "O": "NITK Surathkal"},
        applicant=applicant,
        registry=reg,
    )
    assert res_app.role == SignerRole.APPLICANT
    assert res_app.effective_trust_level == TrustLevel.UNVERIFIED_CLAIM

    # 2. Matching issuer officer
    res_iss = disambiguate_signer(
        {"CN": "Chief Fire Officer", "O": "Directorate of Fire and Emergency Services"},
        applicant=applicant,
        registry=reg,
        is_valid_sig=True,
        is_trusted_chain=True,
    )
    assert res_iss.role == SignerRole.ISSUER_OFFICER
    assert res_iss.effective_trust_level == TrustLevel.CRYPTOGRAPHIC

    # 3. Impersonation attempt: Applicant tries to claim Issuer org
    # If applicant name is present, applicant role takes precedence
    res_impersonation = disambiguate_signer(
        {"CN": "Prof. Rao", "O": "All India Council for Technical Education"},
        applicant=applicant,
        registry=reg,
    )
    assert res_impersonation.role == SignerRole.APPLICANT
    assert res_impersonation.effective_trust_level == TrustLevel.UNVERIFIED_CLAIM


# ---------------------------------------------------------------------------
# Deliverable 3: Signed QR Verification Tests
# ---------------------------------------------------------------------------

@pytest.fixture
def qr_keyring():
    """Setup a test Keyring with Ed25519 and ECDSA keys."""
    # Ed25519
    ed_priv = ed25519.Ed25519PrivateKey.generate()
    ed_pub_pem = ed_priv.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    # ECDSA
    ec_priv = ec.generate_private_key(ec.SECP256R1())
    ec_pub_pem = ec_priv.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    kr = Keyring()
    kr.add_key(
        KeyringEntry(
            key_id="test-aicte-ed25519",
            algorithm="Ed25519",
            issuer="All India Council for Technical Education",
            role="ISSUER_OFFICER",
            public_key_pem=ed_pub_pem,
            public_key_obj=ed_priv.public_key(),
        )
    )
    kr.add_key(
        KeyringEntry(
            key_id="test-fire-ecdsa",
            algorithm="ECDSA",
            curve="SECP256R1",
            issuer="Directorate of Fire Services",
            role="ISSUER_OFFICER",
            public_key_pem=ec_pub_pem,
            public_key_obj=ec_priv.public_key(),
        )
    )
    return {
        "keyring": kr,
        "ed_priv": ed_priv,
        "ec_priv": ec_priv,
    }


def test_qr_verification_roundtrip_ed25519(qr_keyring):
    """Test full cycle: Ed25519 sign -> QR image render -> OpenCV decode -> verify."""
    kr = qr_keyring["keyring"]
    ed_priv = qr_keyring["ed_priv"]

    doc_data = {
        "noc_number": "AICTE-2024-NOC-4921",
        "institution": "Apex Engineering Institute",
        "valid_until": "2027-03-31",
        "approved_intake": 420,
    }

    # 1. Sign
    payload = sign_qr_payload(doc_data, ed_priv, key_id="test-aicte-ed25519")

    # 2. Render to QR PNG image
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(json.dumps(payload))
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")
    qr_png_bytes = buf.getvalue()

    # 3. Decode QR code with OpenCV
    decoded_texts = decode_qr_from_image(qr_png_bytes)
    assert len(decoded_texts) == 1

    # 4. Verify
    res = verify_qr_payload(decoded_texts[0], keyring=kr)
    assert res.status == QRVerificationStatus.VALID
    assert res.is_tampered is False
    assert res.key_id == "test-aicte-ed25519"
    assert res.issuer == "All India Council for Technical Education"

    # EvidenceItem check
    ev = res.evidence_item
    assert ev is not None
    assert ev.effective_trust_level() == TrustLevel.CRYPTOGRAPHIC
    assert ev.trust_rank == 60


def test_qr_verification_roundtrip_ecdsa(qr_keyring):
    """Test full cycle with ECDSA public key."""
    kr = qr_keyring["keyring"]
    ec_priv = qr_keyring["ec_priv"]

    data = {"permit_id": "FIRE-NOC-2024-88", "status": "APPROVED"}
    payload = sign_qr_payload(data, ec_priv, key_id="test-fire-ecdsa")

    res = verify_qr_payload(payload, keyring=kr)
    assert res.status == QRVerificationStatus.VALID
    assert res.is_tampered is False
    assert res.evidence_item.effective_trust_level() == TrustLevel.CRYPTOGRAPHIC


def test_qr_verification_tampered_payload(qr_keyring):
    """Tampering with payload data must return INVALID and STRUCTURAL_FORENSIC trust."""
    kr = qr_keyring["keyring"]
    ed_priv = qr_keyring["ed_priv"]

    data = {"intake": 300}
    payload = sign_qr_payload(data, ed_priv, key_id="test-aicte-ed25519")

    # Tamper with data
    payload["data"]["intake"] = 9000

    res = verify_qr_payload(payload, keyring=kr)
    assert res.status == QRVerificationStatus.INVALID
    assert res.is_tampered is True
    assert res.evidence_item.effective_trust_level() == TrustLevel.STRUCTURAL_FORENSIC
    assert res.evidence_item.trust_rank == 20


def test_qr_verification_unknown_issuer(qr_keyring):
    """Unregistered key_id must return UNKNOWN_ISSUER."""
    kr = qr_keyring["keyring"]
    ed_priv = qr_keyring["ed_priv"]

    payload = sign_qr_payload({"foo": "bar"}, ed_priv, key_id="unregistered-foreign-key")
    res = verify_qr_payload(payload, keyring=kr)

    assert res.status == QRVerificationStatus.UNKNOWN_ISSUER
    assert res.is_tampered is False
    assert res.evidence_item.effective_trust_level() == TrustLevel.UNVERIFIED_CLAIM


# ---------------------------------------------------------------------------
# Deliverable 4: Photo Integrity & Geofencing Tests
# ---------------------------------------------------------------------------

def _create_test_photo(
    lat_dms: tuple[float, float, float] | None = None,
    lon_dms: tuple[float, float, float] | None = None,
    software: str | None = None,
    make: str = "Samsung",
    model: str = "Galaxy S23",
    strip_exif: bool = False,
) -> bytes:
    """Helper to create a JPEG image with customizable EXIF tags."""
    img = Image.new("RGB", (200, 200), color=(120, 150, 180))
    buf = io.BytesIO()

    if strip_exif:
        img.save(buf, format="JPEG")
        return buf.getvalue()

    exif = img.getexif()
    if make:
        exif[ExifTags.Base.Make] = make
    if model:
        exif[ExifTags.Base.Model] = model
    if software:
        exif[ExifTags.Base.Software] = software
    exif[ExifTags.Base.DateTimeOriginal] = "2024:10:15 11:30:00"
    exif[ExifTags.Base.DateTime] = "2024:10:15 11:30:00"

    if lat_dms and lon_dms:
        gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
        gps_ifd[ExifTags.GPS.GPSLatitude] = lat_dms
        gps_ifd[ExifTags.GPS.GPSLatitudeRef] = "N"
        gps_ifd[ExifTags.GPS.GPSLongitude] = lon_dms
        gps_ifd[ExifTags.GPS.GPSLongitudeRef] = "E"

    img.save(buf, format="JPEG", exif=exif)
    return buf.getvalue()


def test_photo_integrity_geofence_inside():
    """Photo GPS coordinates inside declared campus boundary pass geofencing."""
    # Bengaluru campus boundary polygon: [lon, lat]
    campus_poly = Polygon([
        (77.5900, 12.9700),
        (77.6000, 12.9700),
        (77.6000, 12.9800),
        (77.5900, 12.9800),
    ])

    # Photo taken inside campus at 12.9750°N, 77.5950°E
    # DMS: 12 deg 58 min 30 sec = 12 + 58/60 + 30/3600 = 12.9750
    # Lon DMS: 77 deg 35 min 42 sec = 77 + 35/60 + 42/3600 = 77.5950
    photo_bytes = _create_test_photo(
        lat_dms=(12.0, 58.0, 30.0),
        lon_dms=(77.0, 35.0, 42.0),
    )

    report = verify_photo_integrity(
        photo_bytes,
        campus_polygon=campus_poly,
        source_document_name="Engineering_Block_Photo.jpg",
    )

    assert report.is_tampered is False
    assert report.geofence.checked is True
    assert report.geofence.is_inside is True
    assert report.assessed_trust_level == TrustLevel.RECORD
    assert report.evidence_item.effective_trust_level() == TrustLevel.RECORD


def test_photo_integrity_geofence_outside_violation():
    """Photo GPS coordinates outside declared campus boundary fail geofencing."""
    campus_poly = Polygon([
        (77.5900, 12.9700),
        (77.6000, 12.9700),
        (77.6000, 12.9800),
        (77.5900, 12.9800),
    ])

    # Photo taken 5 km away at 13.0100°N, 77.6500°E
    # 13°0'36" = 13.0100, 77°39'0" = 77.6500
    photo_bytes = _create_test_photo(
        lat_dms=(13.0, 0.0, 36.0),
        lon_dms=(77.0, 39.0, 0.0),
    )

    report = verify_photo_integrity(
        photo_bytes,
        campus_polygon=campus_poly,
        source_document_name="Offsite_Photo.jpg",
    )

    assert report.geofence.checked is True
    assert report.geofence.is_inside is False
    assert report.is_tampered is True
    assert report.geofence.distance_meters > 1000
    assert report.assessed_trust_level == TrustLevel.STRUCTURAL_FORENSIC
    assert report.evidence_item.effective_trust_level() == TrustLevel.STRUCTURAL_FORENSIC


def test_photo_integrity_metadata_stripping_and_photoshop_detection():
    """Detect stripped EXIF and Photoshop manipulation tags."""
    # 1. Stripped EXIF
    stripped_bytes = _create_test_photo(strip_exif=True)
    report_stripped = verify_photo_integrity(stripped_bytes)
    assert report_stripped.exif.is_stripped is True
    assert any("stripped" in f.lower() for f in report_stripped.tamper_flags)

    # 2. Photo edited in Photoshop
    ps_bytes = _create_test_photo(
        lat_dms=(12.0, 58.0, 30.0),
        lon_dms=(77.0, 35.0, 42.0),
        software="Adobe Photoshop 2024 (Windows)",
    )
    report_ps = verify_photo_integrity(ps_bytes)
    assert report_ps.is_tampered is True
    assert any("photoshop" in f.lower() for f in report_ps.tamper_flags)
    assert report_ps.assessed_trust_level == TrustLevel.STRUCTURAL_FORENSIC


def test_c2pa_reader_graceful_handling():
    """Ensure c2pa validation handles photos with or without manifests gracefully."""
    plain_photo = _create_test_photo(lat_dms=(12.0, 58.0, 30.0), lon_dms=(77.0, 35.0, 42.0))
    res = validate_c2pa(plain_photo)
    assert res.has_manifest is False
    assert "no c2pa manifest" in res.details.lower() or "not found" in res.details.lower()


# ---------------------------------------------------------------------------
# Deliverable 3 & Acceptance: FastAPI /scan Endpoint Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_scan_endpoint_returns_mobile_viewport():
    """GET /scan must serve responsive mobile-friendly HTML with camera upload."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/scan")

    assert response.status_code == 200
    html = response.text
    # Assert mobile viewport tag exists
    assert '<meta name="viewport"' in html
    # Assert camera file input exists
    assert 'type="file"' in html
    assert 'accept="image/*"' in html
    assert 'capture="environment"' in html
    # Assert verification status elements
    assert "VALID" in html or "status-VALID" in html
    assert "Nirikshan" in html


@pytest.mark.asyncio
async def test_post_scan_endpoint_image_upload(qr_keyring):
    """POST /scan with uploaded QR code image returns VALID verification."""
    kr = qr_keyring["keyring"]
    ed_priv = qr_keyring["ed_priv"]

    payload = sign_qr_payload(
        {"approval_id": "AICTE-2024-APX-01", "status": "APPROVED"},
        ed_priv,
        key_id="test-aicte-ed25519",
    )

    qr_img = qrcode.make(json.dumps(payload))
    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")
    buf.seek(0)

    # Mock keyring inside Keyring instance or ensure key is present
    from unittest.mock import patch

    with patch("nirikshan.api.routes_scan.Keyring", return_value=kr):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            files = {"file": ("qr_code.png", buf.getvalue(), "image/png")}
            response = await ac.post("/scan", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "VALID"
    assert data["trust_ladder_level"] == "CRYPTOGRAPHIC"
    assert data["trust_rank"] == 60
    assert data["is_tampered"] is False
    assert data["data"]["approval_id"] == "AICTE-2024-APX-01"


@pytest.mark.asyncio
async def test_post_scan_endpoint_invalid_and_unknown_issuer(qr_keyring):
    """POST /scan handles tampered payload and unknown issuer."""
    kr = qr_keyring["keyring"]
    ed_priv = qr_keyring["ed_priv"]

    from unittest.mock import patch

    with patch("nirikshan.api.routes_scan.Keyring", return_value=kr):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # 1. Unknown issuer
            payload_unk = sign_qr_payload({"x": 1}, ed_priv, key_id="unknown-999")
            res_unk = await ac.post("/scan", json=payload_unk)
            assert res_unk.status_code == 200
            assert res_unk.json()["status"] == "UNKNOWN_ISSUER"

            # 2. Tampered signature
            payload_tampered = sign_qr_payload({"x": 1}, ed_priv, key_id="test-aicte-ed25519")
            payload_tampered["data"]["x"] = 999
            res_inv = await ac.post("/scan", json=payload_tampered)
            assert res_inv.status_code == 200
            assert res_inv.json()["status"] == "INVALID"
            assert res_inv.json()["is_tampered"] is True
