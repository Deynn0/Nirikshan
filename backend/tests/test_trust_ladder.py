"""Tests verifying non-negotiable Trust Ladder principles."""

from nirikshan.schemas.citation import HandbookCitation
from nirikshan.schemas.finding import Finding, VerificationStatus
from nirikshan.trust.ladder import (
    TRUST_RANKS,
    BoundingBox,
    EvidenceItem,
    TrustLevel,
)


def test_trust_ladder_strict_ordering() -> None:
    """Evidence must be ranked Cryptographic > Issuer > Record > Rule > Structural/Forensic > Model > Claim."""
    assert TRUST_RANKS[TrustLevel.CRYPTOGRAPHIC] > TRUST_RANKS[TrustLevel.ISSUER]
    assert TRUST_RANKS[TrustLevel.ISSUER] > TRUST_RANKS[TrustLevel.RECORD]
    assert TRUST_RANKS[TrustLevel.RECORD] > TRUST_RANKS[TrustLevel.RULE]
    assert TRUST_RANKS[TrustLevel.RULE] > TRUST_RANKS[TrustLevel.STRUCTURAL_FORENSIC]
    assert TRUST_RANKS[TrustLevel.STRUCTURAL_FORENSIC] > TRUST_RANKS[TrustLevel.MODEL]
    assert TRUST_RANKS[TrustLevel.MODEL] > TRUST_RANKS[TrustLevel.UNVERIFIED_CLAIM]


def test_applicant_self_attestation_never_verified() -> None:
    """Non-Negotiable Principle 1: Applicant self-attestation NEVER counts as verified."""
    evidence = EvidenceItem(
        evidence_id="ev-claim-001",
        trust_level=TrustLevel.RECORD,  # Claiming record-level
        source_type="AFFIDAVIT_SELF_DECLARATION",
        description="Affidavit stating campus possesses 5 acres of land",
        source_document_id="doc-affidavit-1",
        source_document_name="self_declaration_affidavit.pdf",
        is_self_attested=True,
        verification_method="NOTARY_AFFIDAVIT_ONLY",
    )

    # Effective trust level MUST collapse to UNVERIFIED_CLAIM
    assert evidence.effective_trust_level() == TrustLevel.UNVERIFIED_CLAIM
    assert evidence.is_decisive is False


def test_model_output_is_advisory_only_cannot_decide_pass_or_fail() -> None:
    """Non-Negotiable Principle 1: Model output is advisory only and can never be the sole reason for a pass or fail."""
    bbox = BoundingBox(page=1, x=50.0, y=100.0, width=200.0, height=40.0)
    model_evidence = EvidenceItem(
        evidence_id="ev-model-001",
        trust_level=TrustLevel.MODEL,
        source_type="OCR_VISION_PREDICTION",
        description="OCR model detected 5.2 acres text",
        raw_value=5.2,
        source_document_id="doc-scan-1",
        source_document_name="unverified_scan.pdf",
        bounding_box=bbox,
        verification_method="OCR_HEURISTIC_PREDICTOR",
    )

    finding = Finding(
        finding_id="fnd-test-01",
        rule_id="AICTE-2024-LAND-001",
        rule_name="Minimum Land Requirement",
        category="Land",
        status=VerificationStatus.PASS,  # Model attempted to pass
        summary="Passed via OCR prediction",
        details="Clause 4.1",
        handbook_citation=HandbookCitation(
            handbook="AICTE Approval Process Handbook 2024-2027",
            clause="Clause 4.1",
            page=42,
            edition="2024-2027",
        ),
        evidence_list=[model_evidence],
    )

    # Validate trust integrity must intercept and downgrade
    finding.validate_trust_integrity()

    assert finding.status == VerificationStatus.MANUAL_REVIEW_REQUIRED
    assert finding.is_model_advisory_only is True
    assert any("Model outputs" in note for note in finding.advisory_notes)
