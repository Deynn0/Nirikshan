"""Document metadata and forensic schema."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from nirikshan.trust.ladder import TrustLevel


class DocumentType(StrEnum):
    """Document classification types in regulatory dossier."""

    LAND_SALE_DEED = "LAND_SALE_DEED"
    LAND_LEASE_DEED = "LAND_LEASE_DEED"
    LAND_USE_CONVERSION_CERT = "LAND_USE_CONVERSION_CERT"
    BUILDING_PLAN_APPROVED = "BUILDING_PLAN_APPROVED"
    BUILDING_COMPLETION_CERT = "BUILDING_COMPLETION_CERT"
    FIRE_SAFETY_NOC = "FIRE_SAFETY_NOC"
    BARRIER_FREE_CERT = "BARRIER_FREE_CERT"
    FDR_RECEIPT = "FDR_RECEIPT"
    TRUST_REGISTRATION_CERT = "TRUST_REGISTRATION_CERT"
    FACULTY_MASTER_LIST = "FACULTY_MASTER_LIST"
    AFFIDAVIT_SELF_DECLARATION = "AFFIDAVIT_SELF_DECLARATION"
    UNKNOWN = "UNKNOWN"


class ForensicReport(BaseModel):
    """Forensic and cryptographic verification of an untrusted file."""

    document_id: str
    file_name: str
    sha256_hash: str
    file_size_bytes: int
    page_count: int
    is_tampered: bool = False
    tamper_flags: list[str] = Field(default_factory=list)
    has_digital_signature: bool = False
    signature_valid: bool | None = None
    signer_name: str | None = None
    signer_org: str | None = None
    signature_time: datetime | None = None
    creation_date: datetime | None = None
    modification_date: datetime | None = None
    producer: str | None = None
    incremental_updates_count: int = 0
    font_anomalies: list[str] = Field(default_factory=list)
    assessed_trust_level: TrustLevel = TrustLevel.STRUCTURAL_FORENSIC


class DocumentRecord(BaseModel):
    """Metadata record of an uploaded institutional document."""

    document_id: str
    dossier_id: str
    file_name: str
    doc_type: DocumentType
    title: str
    page_count: int
    forensic: ForensicReport
    extracted_text_preview: str = ""
    is_self_attested: bool = False
