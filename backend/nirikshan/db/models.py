"""SQLAlchemy ORM models for Nirikshan state store."""

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class DossierModel(Base):
    """Institutional application dossier under scrutiny."""

    __tablename__ = "dossiers"

    dossier_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    institution_name: Mapped[str] = mapped_column(String(255), nullable=False)
    application_number: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    program: Mapped[str] = mapped_column(String(128), default="Engineering & Technology")
    level: Mapped[str] = mapped_column(String(64), default="Under Graduate (UG)")
    institution_type: Mapped[str] = mapped_column(String(128), default="Private-Self Financing")
    location_type: Mapped[str] = mapped_column(String(64), default="Urban")
    intake_proposed: Mapped[int] = mapped_column(Integer, default=300)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    overall_status: Mapped[str] = mapped_column(String(32), default="INCONCLUSIVE")
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    summary: Mapped[str] = mapped_column(Text, default="Awaiting verification.")
    extracted_params_json: Mapped[str] = mapped_column(Text, default="{}")

    documents: Mapped[list["DocumentModel"]] = relationship(
        "DocumentModel", back_populates="dossier", cascade="all, delete-orphan"
    )
    findings: Mapped[list["FindingModel"]] = relationship(
        "FindingModel", back_populates="dossier", cascade="all, delete-orphan"
    )
    entity_edges: Mapped[list["ApplicationEntityEdgeModel"]] = relationship(
        "ApplicationEntityEdgeModel", back_populates="dossier", cascade="all, delete-orphan"
    )

    def get_extracted_params(self) -> dict[str, Any]:
        return json.loads(self.extracted_params_json) if self.extracted_params_json else {}

    def set_extracted_params(self, params: dict[str, Any]) -> None:
        self.extracted_params_json = json.dumps(params)


class DocumentModel(Base):
    """Document uploaded and quarantined for an application dossier."""

    __tablename__ = "documents"

    document_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    dossier_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("dossiers.dossier_id"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    quarantine_path: Mapped[str] = mapped_column(String(512), nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, default=1)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    is_self_attested: Mapped[bool] = mapped_column(Boolean, default=False)
    is_tampered: Mapped[bool] = mapped_column(Boolean, default=False)
    forensic_json: Mapped[str] = mapped_column(Text, default="{}")
    text_preview: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    dossier: Mapped[DossierModel] = relationship("DossierModel", back_populates="documents")


class FindingModel(Base):
    """Explainable scrutiny finding attached to a regulatory rule."""

    __tablename__ = "findings"

    finding_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    dossier_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("dossiers.dossier_id"), nullable=False
    )
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    handbook_citation_json: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_list_json: Mapped[str] = mapped_column(Text, default="[]")
    bounding_box_json: Mapped[str] = mapped_column(Text, default="{}")
    advisory_notes_json: Mapped[str] = mapped_column(Text, default="[]")
    is_model_advisory_only: Mapped[bool] = mapped_column(Boolean, default=False)
    needs_verification: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    dossier: Mapped[DossierModel] = relationship("DossierModel", back_populates="findings")


class EntityIndexModel(Base):
    """Extracted cross-application regulatory entity.

    Supports faculty salted hash, certificate numbers, file SHA-256s,
    photo perceptual hashes, seal perceptual hashes, land registration numbers,
    and declared addresses.
    """

    __tablename__ = "entity_index"

    entity_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_value: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    raw_label: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    edges: Mapped[list["ApplicationEntityEdgeModel"]] = relationship(
        "ApplicationEntityEdgeModel", back_populates="entity", cascade="all, delete-orphan"
    )

    def get_metadata(self) -> dict[str, Any]:
        return json.loads(self.metadata_json) if self.metadata_json else {}

    def set_metadata(self, meta: dict[str, Any]) -> None:
        self.metadata_json = json.dumps(meta)


class ApplicationEntityEdgeModel(Base):
    """Cross-application graph edge linking a dossier to an entity with relation 'uses'."""

    __tablename__ = "application_entity_edges"

    edge_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    dossier_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("dossiers.dossier_id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("entity_index.entity_id", ondelete="CASCADE"), nullable=False, index=True
    )
    relation: Mapped[str] = mapped_column(String(32), default="uses")
    context_label: Mapped[str] = mapped_column(String(255), default="")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    dossier: Mapped[DossierModel] = relationship("DossierModel", back_populates="entity_edges")
    entity: Mapped[EntityIndexModel] = relationship("EntityIndexModel", back_populates="edges")

    def get_metadata(self) -> dict[str, Any]:
        return json.loads(self.metadata_json) if self.metadata_json else {}

    def set_metadata(self, meta: dict[str, Any]) -> None:
        self.metadata_json = json.dumps(meta)


class AuditLogModel(Base):
    """Cryptographically chained immutable audit log entry for regulatory evaluations."""

    __tablename__ = "audit_log"

    entry_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    evaluation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    dossier_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    entry_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[str] = mapped_column(String(64), nullable=False)
    ruleset_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    input_digests_json: Mapped[str] = mapped_column(Text, default="[]")
    model_versions_json: Mapped[str] = mapped_column(Text, default="{}")
    event_payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    def get_input_digests(self) -> list[str]:
        return json.loads(self.input_digests_json) if self.input_digests_json else []

    def set_input_digests(self, digests: list[str]) -> None:
        self.input_digests_json = json.dumps(digests)

    def get_model_versions(self) -> dict[str, str]:
        return json.loads(self.model_versions_json) if self.model_versions_json else {}

    def set_model_versions(self, versions: dict[str, str]) -> None:
        self.model_versions_json = json.dumps(versions)

    def get_event_payload(self) -> dict[str, Any]:
        return json.loads(self.event_payload_json) if self.event_payload_json else {}

    def set_event_payload(self, payload: dict[str, Any]) -> None:
        self.event_payload_json = json.dumps(payload)


class JobModel(Base):
    """Asynchronous background verification job with stage-by-stage tracking."""

    __tablename__ = "evaluation_jobs"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    dossier_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("dossiers.dossier_id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True)
    current_stage: Mapped[str] = mapped_column(String(32), default="ingest")
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    stage_message: Mapped[str] = mapped_column(String(255), default="")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def get_result(self) -> dict[str, Any] | None:
        return json.loads(self.result_json) if self.result_json else None

    def set_result(self, result: dict[str, Any]) -> None:
        self.result_json = json.dumps(result)


class UserModel(Base):
    """User principal for role-based scrutiny access control."""

    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="applicant", index=True)
    full_name: Mapped[str] = mapped_column(String(128), default="")
    institution_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))


