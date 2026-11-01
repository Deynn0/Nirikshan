"""Trust ladder package defining evidential hierarchy and validation."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TrustLevel(StrEnum):
    """Ordinal trust levels ranked from most authoritative to advisory."""

    CRYPTOGRAPHIC = "CRYPTOGRAPHIC"  # Rank 1: X.509 PKI, signed QR, cryptographic hashes
    ISSUER = "ISSUER"  # Rank 2: Verified municipal / authority endorsement
    RECORD = "RECORD"  # Rank 3: Official sub-registrar deed, RoR, government gazette
    RULE = "RULE"  # Rank 4: Deterministic mathematical/logical evaluation
    STRUCTURAL_FORENSIC = "STRUCTURAL_FORENSIC"  # Rank 5: PDF metadata, font tampering, ELA
    MODEL = "MODEL"  # Rank 6: Local OCR / Vision / Heuristics (ADVISORY ONLY)
    UNVERIFIED_CLAIM = "UNVERIFIED_CLAIM"  # Rank 0: Applicant self-attestation / affidavits


# EvidenceLevel is synonymous with TrustLevel (Trust Ladder)
EvidenceLevel = TrustLevel


# Strict ordinal ranks for comparison
TRUST_RANKS: dict[TrustLevel, int] = {
    TrustLevel.CRYPTOGRAPHIC: 60,
    TrustLevel.ISSUER: 50,
    TrustLevel.RECORD: 40,
    TrustLevel.RULE: 30,
    TrustLevel.STRUCTURAL_FORENSIC: 20,
    TrustLevel.MODEL: 10,
    TrustLevel.UNVERIFIED_CLAIM: 0,
}


class BoundingBox(BaseModel):
    """Bounding box on a document page (PDF coordinate points)."""

    page: int = Field(..., ge=1, description="1-indexed page number")
    x: float = Field(..., ge=0, description="X coordinate (left)")
    y: float = Field(..., ge=0, description="Y coordinate (top)")
    width: float = Field(..., ge=0, description="Width")
    height: float = Field(..., ge=0, description="Height")

    def to_rect(self) -> tuple[float, float, float, float]:
        """Return (x, y, width, height) tuple."""
        return (self.x, self.y, self.width, self.height)


class EvidenceItem(BaseModel):
    """Atomic piece of evidence supporting a finding."""

    evidence_id: str
    trust_level: TrustLevel
    source_type: str = Field(..., description="e.g. 'Sale Deed', 'Building Plan', 'Fire NOC'")
    description: str
    raw_value: Any = None
    source_document_id: str
    source_document_name: str
    page_number: int | None = None
    bounding_box: BoundingBox | None = None
    is_self_attested: bool = False
    is_tampered: bool = False
    verification_method: str = Field(
        ..., description="e.g. 'PKI_X509', 'SUB_REGISTRAR_SEAL', 'OCR_ADVISORY'"
    )

    def effective_trust_level(self) -> TrustLevel:
        """Enforce non-negotiable trust constraints:

        1. Applicant self-attestation is NEVER counted as verified (forces UNVERIFIED_CLAIM).
        2. Tampered files cannot provide valid record/cryptographic trust.
        """
        if self.is_self_attested:
            return TrustLevel.UNVERIFIED_CLAIM
        if self.is_tampered:
            return TrustLevel.STRUCTURAL_FORENSIC
        return self.trust_level

    @property
    def trust_rank(self) -> int:
        return TRUST_RANKS[self.effective_trust_level()]

    @property
    def is_decisive(self) -> bool:
        """Returns True if this evidence is eligible to independently decide pass/fail.

        Model outputs and self-attestations are NEVER decisive.
        """
        eff = self.effective_trust_level()
        return eff not in (
            TrustLevel.MODEL,
            TrustLevel.UNVERIFIED_CLAIM,
            TrustLevel.STRUCTURAL_FORENSIC,
        )
