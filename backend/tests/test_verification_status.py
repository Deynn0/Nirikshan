"""Verification & Rectification Workflow: Officer review status transitions (reviewed vs. verified).

Covers:
- Scrutiny status lifecycle transitions (UNVERIFIED, MANUAL_REVIEW_REQUIRED, REVIEWED, VERIFIED, FLAGGED_TAMPER)
- Strict boundary between officer review (human scrutiny completed) and verification (cryptographic / institutional registry guarantee)
- Non-negotiable block: self-attestation and ML advisory outputs cannot transition to VERIFIED without root anchors
"""

from __future__ import annotations

import pytest

from nirikshan.schemas.citation import HandbookCitation
from nirikshan.schemas.dossier import ApplicationDossier
from nirikshan.schemas.finding import Finding, VerificationStatus
from nirikshan.trust.ladder import (
    BoundingBox,
    EvidenceItem,
    TrustLevel,
)


def test_status_transition_manual_review_on_unverified_claim() -> None:
    """Findings based on applicant claims cannot advance to VERIFIED directly."""
    ev = EvidenceItem(
        evidence_id="ev-claim-01",
        trust_level=TrustLevel.RECORD,
        source_type="AFFIDAVIT",
        description="Affidavit claiming 10,000 sq.m built-up area",
        source_document_id="doc-aff-01",
        source_document_name="affidavit.pdf",
        is_self_attested=True,
        verification_method="NOTARY_AFFIDAVIT",
    )
    finding = Finding(
        finding_id="fnd-stat-01",
        rule_id="AICTE-2024-AREA-001",
        rule_name="Built-Up Area Norms",
        category="Infrastructure",
        status=VerificationStatus.PASS,
        summary="Passed via affidavit",
        details="Clause 4.2",
        handbook_citation=HandbookCitation(
            clause="Clause 4.2",
            page=45,
        ),
        evidence_list=[ev],
    )
    finding.validate_trust_integrity()
    assert finding.status == VerificationStatus.MANUAL_REVIEW_REQUIRED
    assert finding.evidence_level == TrustLevel.UNVERIFIED_CLAIM


def test_status_transition_reviewed_to_verified_requires_cryptographic_anchor() -> None:
    """Only cryptographic or issuer authority anchors can satisfy VERIFIED status."""
    crypto_ev = EvidenceItem(
        evidence_id="ev-crypto-01",
        trust_level=TrustLevel.CRYPTOGRAPHIC,
        source_type="SIGNED_FIRE_NOC",
        description="Digitally signed NOC from Fire Directorate",
        source_document_id="doc-fire-01",
        source_document_name="fire_noc.pdf",
        verification_method="X509_PKI_VERIFIED",
    )
    finding = Finding(
        finding_id="fnd-stat-02",
        rule_id="AICTE-2024-SAFE-001",
        rule_name="Fire & Safety Compliance",
        category="Safety",
        status=VerificationStatus.PASS,
        summary="Verified through digital signature",
        details="Clause 6.1",
        handbook_citation=HandbookCitation(
            clause="Clause 6.1",
            page=70,
        ),
        evidence_list=[crypto_ev],
    )
    finding.validate_trust_integrity()
    assert finding.status == VerificationStatus.PASS
    assert finding.evidence_level == TrustLevel.CRYPTOGRAPHIC


def test_tamper_status_overrides_all_other_states() -> None:
    """Tamper signals prevent decisive pass and require escalation."""
    tampered_ev = EvidenceItem(
        evidence_id="ev-tampered-01",
        trust_level=TrustLevel.STRUCTURAL_FORENSIC,
        source_type="LAND_DEED",
        description="Altered land deed with incremental update anomaly",
        source_document_id="doc-deed-01",
        source_document_name="land_deed.pdf",
        is_tampered=True,
        verification_method="FORENSIC_PARSER",
    )
    assert tampered_ev.is_decisive is False

    finding = Finding(
        finding_id="fnd-stat-03",
        rule_id="AICTE-2024-LAND-001",
        rule_name="Minimum Land Requirement",
        category="Land",
        status=VerificationStatus.PASS,
        summary="Claimed pass before tamper check",
        details="Clause 4.1",
        handbook_citation=HandbookCitation(
            clause="Clause 4.1",
            page=42,
        ),
        evidence_list=[tampered_ev],
    )
    finding.validate_trust_integrity()
    assert finding.status == VerificationStatus.MANUAL_REVIEW_REQUIRED
    assert finding.is_model_advisory_only is True


def test_dossier_overall_status_aggregation() -> None:
    """Dossier overall status combines individual findings deterministically."""
    dossier = ApplicationDossier(
        dossier_id="dos-status-01",
        institution_name="Sunrise College",
        application_number="AICTE/2024/SUN/001",
        program="Management",
        level="Post Graduate (PG)",
        institution_type="Private-Self Financing",
        location_type="Urban",
        intake_proposed=120,
    )
    assert dossier.overall_status == "INCONCLUSIVE"
