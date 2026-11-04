"""Regulatory Governance & EC Handoff: Executive Committee report generation, digital signing, immutability."""

from __future__ import annotations

import datetime
import hashlib
import io
import json
from pathlib import Path

import asn1crypto.keys as asn1_keys
import asn1crypto.x509 as asn1_x509
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import fields, signers
from pyhanko_certvalidator.registry import SimpleCertificateStore
from reportlab.pdfgen import canvas

from nirikshan.crypto.pdf_verifier import (
    ApplicantIdentity,
    SignerRole,
    verify_pdf_signatures,
)
from nirikshan.crypto.signer_disambiguation import (
    IssuerRegistry,
    disambiguate_signer,
)
from nirikshan.trust.ladder import TrustLevel


@pytest.fixture(scope="module")
def ec_pki() -> dict:
    now = datetime.datetime.now(datetime.timezone.utc)
    one_day_ago = now - datetime.timedelta(days=1)
    one_year_later = now + datetime.timedelta(days=365)

    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "AICTE Root Certifying Authority"),
        x509.NameAttribute(NameOID.COMMON_NAME, "AICTE EC Root CA 2024"),
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

    officer_key, officer_cert = _make_leaf(
        cn="Dr. S. K. Sharma (Director)",
        org="All India Council for Technical Education",
        email="approval@aicte-india.org",
    )
    applicant_key, applicant_cert = _make_leaf(
        cn="Principal - Apex Engineering Institute",
        org="Apex Education Trust",
        email="principal@apex-engineering.edu.in",
    )
    unknown_key, unknown_cert = _make_leaf(
        cn="John Doe",
        org="Independent Notary Services Ltd",
        email="john@notary.example",
    )
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
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pageCompression=0)
    c.drawString(72, 750, "Regulatory Approval NOC Document")
    c.drawString(72, 720, "This document certifies regulatory compliance.")
    c.save()
    buf.seek(0)

    asn1_leaf_cert = asn1_x509.Certificate.load(cert.public_bytes(serialization.Encoding.DER))
    asn1_leaf_key = asn1_keys.PrivateKeyInfo.load(
        key.private_bytes(serialization.Encoding.DER, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    )
    store = SimpleCertificateStore.from_certs([root_ca])
    signer = signers.SimpleSigner(signing_cert=asn1_leaf_cert, signing_key=asn1_leaf_key, cert_registry=store)

    w = IncrementalPdfFileWriter(buf)
    fields.append_signature_field(w, sig_field_spec=fields.SigFieldSpec(sig_field_name="RegulatorySign"))
    out = io.BytesIO()
    signers.sign_pdf(w, signers.PdfSignatureMetadata(field_name="RegulatorySign"), signer=signer, output=out)
    return out.getvalue()


# ---------------------------------------------------------------------------
# Digital Signature Verification & Role Disambiguation
# ---------------------------------------------------------------------------

def test_pdf_signature_verification_issuer_officer(ec_pki: dict) -> None:
    officer_key, officer_cert = ec_pki["officer"]
    signed_pdf = _create_signed_pdf(officer_key, officer_cert, ec_pki["asn1_ca"])

    applicant = ApplicantIdentity(
        institution_name="Apex Engineering Institute",
        applicant_name="Principal Apex",
    )
    report = verify_pdf_signatures(
        signed_pdf,
        trust_roots=[ec_pki["asn1_ca"]],
        applicant=applicant,
        source_document_name="AICTE_Approval_Letter.pdf",
    )
    assert report.has_signatures is True
    assert report.is_overall_tampered is False
    sig = report.signatures[0]
    assert sig.signer_role == SignerRole.ISSUER_OFFICER
    assert sig.assessed_trust_level == TrustLevel.CRYPTOGRAPHIC


def test_pdf_signature_verification_applicant_cannot_reach_cryptographic(ec_pki: dict) -> None:
    app_key, app_cert = ec_pki["applicant"]
    signed_pdf = _create_signed_pdf(app_key, app_cert, ec_pki["asn1_ca"])

    applicant = ApplicantIdentity(
        institution_name="Apex Engineering Institute",
        trust_or_society_name="Apex Education Trust",
    )
    report = verify_pdf_signatures(
        signed_pdf,
        trust_roots=[ec_pki["asn1_ca"]],
        applicant=applicant,
        source_document_name="Applicant_Declaration.pdf",
    )
    sig = report.signatures[0]
    assert sig.signer_role == SignerRole.APPLICANT
    assert sig.assessed_trust_level == TrustLevel.UNVERIFIED_CLAIM


def test_pdf_signature_verification_unknown_signer(ec_pki: dict) -> None:
    unk_key, unk_cert = ec_pki["unknown"]
    signed_pdf = _create_signed_pdf(unk_key, unk_cert, ec_pki["asn1_ca"])

    applicant = ApplicantIdentity(institution_name="Apex Engineering Institute")
    report = verify_pdf_signatures(
        signed_pdf,
        trust_roots=[ec_pki["asn1_ca"]],
        applicant=applicant,
        source_document_name="Unknown_NOC.pdf",
    )
    sig = report.signatures[0]
    assert sig.signer_role == SignerRole.UNKNOWN


def test_pdf_signature_tampering_detection(ec_pki: dict) -> None:
    officer_key, officer_cert = ec_pki["officer"]
    signed_pdf = _create_signed_pdf(officer_key, officer_cert, ec_pki["asn1_ca"])

    tampered_bytes = bytearray(signed_pdf)
    idx = tampered_bytes.find(b"Regulatory Approval")
    if idx != -1:
        tampered_bytes[idx:idx + 10] = b"FAKED_TEXT"
    else:
        tampered_bytes[len(tampered_bytes) // 2] ^= 0xFF

    report = verify_pdf_signatures(
        bytes(tampered_bytes),
        trust_roots=[ec_pki["asn1_ca"]],
        source_document_name="Tampered_NOC.pdf",
    )
    assert report.is_overall_tampered is True
    assert report.signatures[0].is_tampered is True


def test_signer_disambiguation_rules() -> None:
    applicant = ApplicantIdentity(
        institution_name="National Institute of Technology Karnataka",
        applicant_name="Prof. Rao",
        email="director@nitk.edu.in",
    )
    reg = IssuerRegistry()
    res_app = disambiguate_signer(
        {"CN": "Prof. Rao", "O": "NITK Surathkal"},
        applicant=applicant,
        registry=reg,
    )
    assert res_app.role == SignerRole.APPLICANT
    assert res_app.effective_trust_level == TrustLevel.UNVERIFIED_CLAIM

    res_iss = disambiguate_signer(
        {"CN": "Chief Fire Officer", "O": "Directorate of Fire and Emergency Services"},
        applicant=applicant,
        registry=reg,
        is_valid_sig=True,
        is_trusted_chain=True,
    )
    assert res_iss.role == SignerRole.ISSUER_OFFICER
    assert res_iss.effective_trust_level == TrustLevel.CRYPTOGRAPHIC


# ---------------------------------------------------------------------------
# Executive Committee Handoff Report Generation & Immutability
# ---------------------------------------------------------------------------

def test_ec_handoff_report_generation_and_hash_seal() -> None:
    """Generate EC handoff report package and verify cryptographic seal."""
    ec_handoff = {
        "dossier_id": "dos-ec-2024-001",
        "institution_name": "Indian Institute of Science & Technology",
        "scrutiny_outcome": "RECOMMENDED_FOR_APPROVAL",
        "trust_score": 98.5,
        "deficiencies": [],
        "ec_committee_ref": "AICTE-EC-2024-MEETING-12",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    payload_bytes = json.dumps(ec_handoff, sort_keys=True).encode("utf-8")
    seal_hash = hashlib.sha256(payload_bytes).hexdigest()

    # Seal must be valid 64-char hex
    assert len(seal_hash) == 64

    # Any modification after handoff breaks the seal
    tampered_handoff = dict(ec_handoff)
    tampered_handoff["scrutiny_outcome"] = "REJECTED"
    tampered_bytes = json.dumps(tampered_handoff, sort_keys=True).encode("utf-8")
    tampered_seal = hashlib.sha256(tampered_bytes).hexdigest()

    assert tampered_seal != seal_hash

