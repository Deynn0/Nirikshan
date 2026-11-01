"""Verification finding schemas."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, computed_field, model_validator

from nirikshan.schemas.citation import HandbookCitation
from nirikshan.trust.ladder import BoundingBox, EvidenceItem, TrustLevel


class VerificationStatus(StrEnum):
    """Scrutiny verification result status."""

    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
    FLAGGED_TAMPER = "FLAGGED_TAMPER"


class Finding(BaseModel):
    """Explainable scrutiny finding attached to a regulatory rule."""

    finding_id: str
    rule_id: str = Field(..., description="Unique deterministic rule ID e.g. 'AICTE-2024-LAND-001'")
    rule_name: str
    category: str = Field(
        ..., description="Regulatory domain (e.g., 'Land', 'Infrastructure', 'Faculty')"
    )
    status: VerificationStatus
    summary: str
    details: str
    handbook_citation: HandbookCitation
    evidence_list: list[EvidenceItem] = Field(default_factory=list)
    primary_bounding_box: BoundingBox | None = None
    advisory_notes: list[str] = Field(default_factory=list)
    is_model_advisory_only: bool = False
    needs_verification: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def highest_trust_level(self) -> TrustLevel:
        """Calculate highest trust level among non-attested evidence."""
        if not self.evidence_list:
            return TrustLevel.UNVERIFIED_CLAIM
        valid_ranks = [e.trust_rank for e in self.evidence_list]
        max_rank = max(valid_ranks)
        for ev in self.evidence_list:
            if ev.trust_rank == max_rank:
                return ev.effective_trust_level()
        return TrustLevel.UNVERIFIED_CLAIM

    @computed_field  # type: ignore[prop-decorator]
    @property
    def evidence_level(self) -> TrustLevel:
        """Ordinal evidence level conforming to the Nirikshan Trust Ladder."""
        return self.highest_trust_level

    @model_validator(mode="after")
    def _enforce_trust_integrity_validator(self) -> Finding:
        """Automatically guarantee that no Model-level or self-attested item can produce a verified PASS or FAIL."""
        self.validate_trust_integrity()
        return self

    def validate_trust_integrity(self) -> None:
        """Enforce Non-Negotiable Principle 1:

        - Model output is ADVISORY ONLY and can never be the sole reason for a PASS or FAIL.
        - Applicant self-attestation cannot justify a PASS.
        """
        if self.status == VerificationStatus.PASS:
            decisive_evidence = [e for e in self.evidence_list if e.is_decisive]
            if not decisive_evidence:
                # If only model or self-attestation is present, or no decisive evidence, downgrade to MANUAL_REVIEW_REQUIRED
                self.status = VerificationStatus.MANUAL_REVIEW_REQUIRED
                self.is_model_advisory_only = True
                self.advisory_notes.append(
                    "Downgraded to MANUAL_REVIEW_REQUIRED: Model outputs or self-attestations cannot solely determine PASS."
                )
        elif self.status == VerificationStatus.FAIL:
            if self.evidence_list and all(not e.is_decisive for e in self.evidence_list):
                # If only model or self-attestation is present, downgrade to MANUAL_REVIEW_REQUIRED
                self.status = VerificationStatus.MANUAL_REVIEW_REQUIRED
                self.is_model_advisory_only = True
                self.advisory_notes.append(
                    "Downgraded to MANUAL_REVIEW_REQUIRED: Model outputs or self-attestations cannot solely determine FAIL."
                )
