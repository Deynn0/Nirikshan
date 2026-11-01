"""Application dossier schema for institutional scrutiny."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from nirikshan.schemas.finding import Finding, VerificationStatus
from nirikshan.schemas.forensic import DocumentRecord


class DossierCreate(BaseModel):
    """Payload to initialize a new application dossier."""

    institution_name: str
    application_number: str
    program: str = Field(default="Engineering & Technology")
    level: str = Field(default="Under Graduate (UG)")
    institution_type: str = Field(default="Private-Self Financing")
    location_type: str = Field(default="Urban", description="Mega City, Metro City, Urban, Rural")
    intake_proposed: int = Field(default=300, ge=1)


class ApplicationDossier(BaseModel):
    """Complete scrutiny dossier with documents and verification findings."""

    dossier_id: str
    institution_name: str
    application_number: str
    program: str
    level: str
    institution_type: str
    location_type: str
    intake_proposed: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    documents: list[DocumentRecord] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    overall_status: VerificationStatus = VerificationStatus.INCONCLUSIVE
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    summary: str = "Awaiting verification."
    extracted_params: dict[str, Any] = Field(default_factory=dict)
