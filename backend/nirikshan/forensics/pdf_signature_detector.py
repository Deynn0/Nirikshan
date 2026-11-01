"""Forensic detector for PDF digital signatures (PAdES / CMS)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from nirikshan.crypto.pdf_verifier import verify_pdf_signatures
from nirikshan.forensics.models import (
    FindingCategory,
    FindingSeverity,
    ForensicFinding,
)

log = logging.getLogger(__name__)


def detect(doc: Any) -> list[ForensicFinding]:
    """Detect and inspect PDF digital signatures for tampering, post-signature mods, and authority trust."""
    findings: list[ForensicFinding] = []

    # Get raw file bytes or path from ParsedDocument
    pdf_bytes = getattr(doc, "raw_bytes", None)
    if not pdf_bytes:
        file_path = getattr(doc, "file_path", None) or getattr(doc.metadata, "file_path", None)
        if file_path and Path(file_path).exists():
            pdf_bytes = Path(file_path).read_bytes()

    if not pdf_bytes:
        return findings

    try:
        report = verify_pdf_signatures(
            pdf_bytes,
            source_document_name=getattr(doc.metadata, "file_name", "document.pdf"),
        )
    except Exception as exc:
        log.warning("Signature detector failed to scan document: %s", exc)
        return findings

    if not report.has_signatures:
        return findings

    for sig in report.signatures:
        if sig.is_tampered:
            for reason in sig.tamper_reasons:
                findings.append(
                    ForensicFinding(
                        detector="pdf_signature_detector",
                        category=FindingCategory.SIGNATURE,
                        severity=FindingSeverity.CRITICAL,
                        title=f"Tampered Digital Signature: {sig.field_name}",
                        description=f"Signature by '{sig.signer_name}' ({sig.signer_org}) failed integrity check: {reason}",
                        evidence={
                            "field_name": sig.field_name,
                            "signer_name": sig.signer_name,
                            "signer_org": sig.signer_org,
                            "coverage": sig.coverage_level,
                            "is_intact": sig.is_intact,
                            "tamper_reasons": sig.tamper_reasons,
                        },
                        trust_level="STRUCTURAL_FORENSIC",
                    )
                )
        elif sig.has_post_signature_modifications:
            findings.append(
                ForensicFinding(
                    detector="pdf_signature_detector",
                    category=FindingCategory.REVISION,
                    severity=FindingSeverity.HIGH,
                    title=f"Post-Signature Modifications: {sig.field_name}",
                    description=f"Incremental revisions were appended after signature by '{sig.signer_name}'. Diff: {sig.diff_summary}",
                    evidence={
                        "field_name": sig.field_name,
                        "coverage": sig.coverage_level,
                        "diff_summary": sig.diff_summary,
                    },
                    trust_level="STRUCTURAL_FORENSIC",
                )
            )
        else:
            findings.append(
                ForensicFinding(
                    detector="pdf_signature_detector",
                    category=FindingCategory.SIGNATURE,
                    severity=FindingSeverity.INFO,
                    title=f"Verified Digital Signature: {sig.field_name}",
                    description=f"Cryptographically valid signature by '{sig.signer_name}' ({sig.signer_org}). Role: {sig.signer_role.value}. Coverage: {sig.coverage_level}.",
                    evidence={
                        "field_name": sig.field_name,
                        "signer_name": sig.signer_name,
                        "signer_org": sig.signer_org,
                        "signer_role": sig.signer_role.value,
                        "coverage": sig.coverage_level,
                        "trust_level": sig.assessed_trust_level.value,
                    },
                    trust_level=sig.assessed_trust_level.value,
                )
            )

    return findings
