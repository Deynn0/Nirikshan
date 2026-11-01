"""PDF Digital Signature (PAdES / CMS) verification module using pyHanko.

Features:
- Validates PAdES/CMS signatures with pyHanko.
- Builds validation chain against bundled roots in `backend/trust/roots/` (or specified directory).
- Performs best-effort offline revocation validation (allow_fetching=False, soft-fail).
- Detects post-signature modifications: signed byte-range coverage vs incremental updates.
- Disambiguates signer role (ISSUER_OFFICER, APPLICANT, UNKNOWN).
- Enforces Trust Ladder non-negotiable principle: applicant-signed document never reaches
  Cryptographic-level trust as issuer proof.
- Maps all results into EvidenceItem.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import asn1crypto.x509
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.validation import (
    PdfSignatureStatus,
    SignatureCoverageLevel,
    validate_pdf_signature,
)
from pyhanko_certvalidator import ValidationContext

from nirikshan.config import settings
from nirikshan.crypto.signer_disambiguation import (
    ApplicantIdentity,
    IssuerRegistry,
    SignerRole,
    disambiguate_signer,
)
from nirikshan.trust.ladder import EvidenceItem, TrustLevel

log = logging.getLogger(__name__)


def load_bundled_trust_roots(roots_dir: Path | None = None) -> list[asn1crypto.x509.Certificate]:
    """Scan trust directory for CA certificates (.cer, .crt, .pem, .der).

    Does not fail if no roots are found. Operators place authentic CCA roots here.
    """
    search_dirs = []
    if roots_dir and roots_dir.exists():
        search_dirs.append(roots_dir)
    if settings.trust_roots_dir.exists() and settings.trust_roots_dir not in search_dirs:
        search_dirs.append(settings.trust_roots_dir)
    if settings.trust_dir.exists() and settings.trust_dir not in search_dirs:
        search_dirs.append(settings.trust_dir)

    certs: list[asn1crypto.x509.Certificate] = []
    for d in search_dirs:
        for ext in ("*.cer", "*.crt", "*.pem", "*.der"):
            for cert_file in d.glob(ext):
                try:
                    data = cert_file.read_bytes()
                    # Check if PEM or DER
                    if b"-----BEGIN CERTIFICATE-----" in data:
                        # Extract all PEM certificates
                        import re
                        pem_blocks = re.findall(
                            rb"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----",
                            data,
                            re.DOTALL,
                        )
                        for block in pem_blocks:
                            try:
                                import ssl
                                der = ssl.PEM_cert_to_DER_cert(block.decode("latin1"))
                                certs.append(asn1crypto.x509.Certificate.load(der))
                            except Exception:
                                pass
                    else:
                        certs.append(asn1crypto.x509.Certificate.load(data))
                except Exception as exc:
                    log.warning("Could not load trust root %s: %s", cert_file.name, exc)

    return certs


@dataclass
class SignatureVerificationDetail:
    """Detailed cryptographic status for a single signature field."""

    field_name: str
    signer_name: str
    signer_org: str
    signer_email: str
    signer_role: SignerRole
    subject_dn: dict[str, str]
    issuer_dn: dict[str, str]
    signing_time: datetime | None
    is_intact: bool
    is_valid: bool
    is_trusted: bool
    coverage_level: str
    has_post_signature_modifications: bool
    is_tampered: bool
    tamper_reasons: list[str]
    diff_policy_passed: bool
    diff_summary: str | None
    revocation_status: str
    assessed_trust_level: TrustLevel
    evidence_item: EvidenceItem | None = None


@dataclass
class PdfVerificationReport:
    """Consolidated signature and integrity report for a PDF."""

    file_path: str
    has_signatures: bool
    signature_count: int
    signatures: list[SignatureVerificationDetail] = field(default_factory=list)
    is_overall_tampered: bool = False
    highest_trust_level: TrustLevel = TrustLevel.STRUCTURAL_FORENSIC
    evidence_items: list[EvidenceItem] = field(default_factory=list)
    summary: str = ""


def _extract_subject_dict(cert: asn1crypto.x509.Certificate | None) -> dict[str, str]:
    if not cert:
        return {}
    native = cert.subject.native
    if isinstance(native, dict):
        res: dict[str, str] = {}
        for k, v in native.items():
            if isinstance(v, list):
                res[str(k)] = ", ".join(str(item) for item in v)
            else:
                res[str(k)] = str(v)
        return res
    return {}


def _extract_issuer_dict(cert: asn1crypto.x509.Certificate | None) -> dict[str, str]:
    if not cert:
        return {}
    native = cert.issuer.native
    if isinstance(native, dict):
        res: dict[str, str] = {}
        for k, v in native.items():
            if isinstance(v, list):
                res[str(k)] = ", ".join(str(item) for item in v)
            else:
                res[str(k)] = str(v)
        return res
    return {}


def verify_pdf_signatures(
    pdf_source: Path | str | bytes | io.BytesIO,
    trust_roots: list[asn1crypto.x509.Certificate] | Path | None = None,
    applicant: ApplicantIdentity | None = None,
    registry: IssuerRegistry | None = None,
    *,
    source_document_id: str = "doc_unknown",
    source_document_name: str = "document.pdf",
    required_role: str | None = None,
) -> PdfVerificationReport:
    """Validate all embedded signatures in a PDF with pyHanko.

    Args:
        pdf_source: File path or raw bytes of PDF.
        trust_roots: List of Certificate objects, or directory containing roots.
        applicant: Declared identity of the applicant institution.
        registry: Issuer registry.
        source_document_id: Nirikshan document ID for evidence tracking.
        source_document_name: Human readable name for evidence tracking.
        required_role: Document authority type required (e.g. "ISSUER").
    """
    if isinstance(pdf_source, (str, Path)):
        file_path_str = str(pdf_source)
        data = Path(pdf_source).read_bytes()
    elif isinstance(pdf_source, io.BytesIO):
        file_path_str = source_document_name
        data = pdf_source.getvalue()
    else:
        file_path_str = source_document_name
        data = pdf_source

    stream = io.BytesIO(data)
    try:
        reader = PdfFileReader(stream)
        embedded_sigs = reader.embedded_signatures
    except Exception as exc:
        return PdfVerificationReport(
            file_path=file_path_str,
            has_signatures=False,
            signature_count=0,
            is_overall_tampered=True,
            highest_trust_level=TrustLevel.STRUCTURAL_FORENSIC,
            summary=f"Failed to read PDF structure or signatures: {exc}",
        )

    # Resolve trust roots
    if isinstance(trust_roots, Path):
        roots = load_bundled_trust_roots(trust_roots)
    elif isinstance(trust_roots, list):
        roots = trust_roots
    else:
        roots = load_bundled_trust_roots()

    # Build offline validation context
    vc = ValidationContext(
        trust_roots=roots,
        allow_fetching=False,          # Airgap / strict offline guarantee
        revocation_mode="soft-fail",    # Best-effort offline revocation
    )

    if not embedded_sigs:
        return PdfVerificationReport(
            file_path=file_path_str,
            has_signatures=False,
            signature_count=0,
            highest_trust_level=TrustLevel.STRUCTURAL_FORENSIC,
            summary="Document contains no digital signatures.",
        )

    sig_details: list[SignatureVerificationDetail] = []
    evidence_items: list[EvidenceItem] = []
    is_any_tampered = False

    for sig_obj in embedded_sigs:
        field_name = sig_obj.field_name or "Signature"
        tamper_reasons: list[str] = []
        has_post_sig_mods = False

        try:
            status: PdfSignatureStatus = validate_pdf_signature(
                sig_obj,
                signer_validation_context=vc,
            )
        except Exception as exc:
            # Complete validation failure indicates corrupt or tampered signature
            tamper_reasons.append(f"Validation crashed: {exc}")
            detail = SignatureVerificationDetail(
                field_name=field_name,
                signer_name="Corrupt / Unreadable",
                signer_org="Unknown",
                signer_email="",
                signer_role=SignerRole.UNKNOWN,
                subject_dn={},
                issuer_dn={},
                signing_time=None,
                is_intact=False,
                is_valid=False,
                is_trusted=False,
                coverage_level="UNCLEAR",
                has_post_signature_modifications=True,
                is_tampered=True,
                tamper_reasons=tamper_reasons,
                diff_policy_passed=False,
                diff_summary="Validation exception",
                revocation_status="UNKNOWN",
                assessed_trust_level=TrustLevel.STRUCTURAL_FORENSIC,
            )
            sig_details.append(detail)
            is_any_tampered = True
            continue

        # 1. Cryptographic intactness
        is_intact = bool(status.intact)
        if not is_intact:
            tamper_reasons.append("Cryptographic byte-range digest mismatch (file was altered after signing).")

        # 2. Coverage analysis
        coverage = status.coverage
        coverage_name = coverage.name if coverage else "UNCLEAR"

        # Check coverage vs incremental updates
        if coverage == SignatureCoverageLevel.ENTIRE_FILE:
            # Clean: no modifications after this signature
            has_post_sig_mods = False
            diff_passed = True
            diff_summary = "Signature covers entire file. No incremental modifications."
        elif coverage == SignatureCoverageLevel.ENTIRE_REVISION:
            # Incremental updates occurred: check diff policy
            diff_res = status.diff_result
            if diff_res is not None and not getattr(diff_res, "valid", True):
                has_post_sig_mods = True
                diff_passed = False
                tamper_reasons.append("Unauthorized document alterations in post-signature incremental update.")
                diff_summary = "Unauthorized modifications in appended revision."
            else:
                has_post_sig_mods = False
                diff_passed = True
                diff_summary = "Legitimate incremental revision (e.g. DSS or visual appearance)."
        else:
            # UNCLEAR or CONTIGUOUS_BLOCK_FROM_START
            has_post_sig_mods = True
            diff_passed = False
            tamper_reasons.append(
                f"Signed byte-range does not cover document revision properly ({coverage_name})."
            )
            diff_summary = f"Byte range coverage anomaly: {coverage_name}"

        # 3. Revocation status
        if getattr(status, "revoked", False):
            tamper_reasons.append("Signer certificate is marked as REVOKED.")
            revocation_str = "REVOKED"
        else:
            revocation_str = "OFFLINE_BEST_EFFORT_PASS"

        is_tampered = not is_intact or has_post_sig_mods or bool(status.revoked)
        if is_tampered:
            is_any_tampered = True

        # 4. Signer identity extraction
        signing_cert = status.signing_cert
        subject_dict = _extract_subject_dict(signing_cert)
        issuer_dict = _extract_issuer_dict(signing_cert)

        signer_name = subject_dict.get("common_name", "Unknown Signer")
        signer_org = subject_dict.get("organization_name", "Unknown Org")
        signer_email = subject_dict.get("email_address", "")
        signing_time = status.signer_reported_dt

        # 5. Signer disambiguation
        is_trusted = bool(status.trusted) and not is_tampered
        is_valid = bool(status.valid) and not is_tampered

        disamb_res = disambiguate_signer(
            subject=subject_dict,
            applicant=applicant,
            registry=registry,
            is_valid_sig=is_valid,
            is_trusted_chain=is_trusted,
            is_tampered=is_tampered,
            document_role_required=required_role,
        )

        role = disamb_res.role
        eff_trust = disamb_res.effective_trust_level

        # Map to EvidenceItem
        ev_id = f"ev-pades-{field_name.lower().replace(' ', '_')}-{uuid4().hex[:6]}"
        evidence = EvidenceItem(
            evidence_id=ev_id,
            trust_level=eff_trust,
            source_type="Digital Signature (PAdES/CMS)",
            description=(
                f"PDF signature field '{field_name}' by '{signer_name}' ({signer_org}). "
                f"Role: {role.value}. Coverage: {coverage_name}. Status: {disamb_res.reason}"
            ),
            raw_value={
                "field_name": field_name,
                "signer_name": signer_name,
                "signer_org": signer_org,
                "signer_role": role.value,
                "is_intact": is_intact,
                "is_valid": is_valid,
                "is_trusted": is_trusted,
                "coverage": coverage_name,
                "revocation_status": revocation_str,
                "is_tampered": is_tampered,
                "tamper_reasons": tamper_reasons,
            },
            source_document_id=source_document_id,
            source_document_name=source_document_name,
            is_self_attested=(role == SignerRole.APPLICANT),
            is_tampered=is_tampered,
            verification_method="PYHANKO_PADES_CMS",
        )
        evidence_items.append(evidence)

        sig_detail = SignatureVerificationDetail(
            field_name=field_name,
            signer_name=signer_name,
            signer_org=signer_org,
            signer_email=signer_email,
            signer_role=role,
            subject_dn=subject_dict,
            issuer_dn=issuer_dict,
            signing_time=signing_time,
            is_intact=is_intact,
            is_valid=is_valid,
            is_trusted=is_trusted,
            coverage_level=coverage_name,
            has_post_signature_modifications=has_post_sig_mods,
            is_tampered=is_tampered,
            tamper_reasons=tamper_reasons,
            diff_policy_passed=diff_passed,
            diff_summary=diff_summary,
            revocation_status=revocation_str,
            assessed_trust_level=eff_trust,
            evidence_item=evidence,
        )
        sig_details.append(sig_detail)

    # Determine highest trust level across non-tampered signatures
    highest_trust = TrustLevel.STRUCTURAL_FORENSIC
    if sig_details:
        from nirikshan.trust.ladder import TRUST_RANKS
        highest_trust = max(
            (s.evidence_item.effective_trust_level() for s in sig_details if s.evidence_item),
            key=lambda t: TRUST_RANKS[t],
            default=TrustLevel.STRUCTURAL_FORENSIC,
        )

    summary_text = (
        f"{len(sig_details)} digital signature(s) verified. "
        f"Tamper detected: {is_any_tampered}. "
        f"Assessed Trust Level: {highest_trust.value}."
    )

    return PdfVerificationReport(
        file_path=file_path_str,
        has_signatures=True,
        signature_count=len(sig_details),
        signatures=sig_details,
        is_overall_tampered=is_any_tampered,
        highest_trust_level=highest_trust,
        evidence_items=evidence_items,
        summary=summary_text,
    )
