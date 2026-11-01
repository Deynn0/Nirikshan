"""Cryptographically hash-chained immutable audit log with tamper verification and evaluation replay."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nirikshan.config import settings
from nirikshan.db.models import AuditLogModel
from nirikshan.engine.rule_evaluator import rule_engine
from nirikshan.schemas.dossier import ApplicationDossier
from nirikshan.schemas.finding import Finding, VerificationStatus
from nirikshan.schemas.forensic import DocumentRecord, DocumentType, ForensicReport

GENESIS_PREV_HASH = "0" * 64


class AuditLogEntry(BaseModel):
    """Pydantic representation of a cryptographically chained audit log entry."""

    entry_id: str
    evaluation_id: str
    dossier_id: str
    sequence: int
    prev_hash: str
    entry_hash: str
    timestamp: str
    ruleset_hash: str
    input_digests: list[str]
    model_versions: dict[str, str]
    event_payload: dict[str, Any]


class ChainVerificationResult(BaseModel):
    """Result of audit hash chain integrity verification."""

    is_valid: bool
    total_entries: int
    head_hash: str | None = None
    broken_index: int | None = None
    reason: str | None = None
    expected_hash: str | None = None
    actual_hash: str | None = None


class ReplayResult(BaseModel):
    """Outcome of replaying a past regulatory evaluation."""

    evaluation_id: str
    is_identical: bool
    original_status: str
    replayed_status: str
    original_risk_score: float
    replayed_risk_score: float
    original_findings_count: int
    replayed_findings_count: int
    diffs: list[str] = Field(default_factory=list)


def get_ruleset_hash(filename: str = "aicte_aph_2024_2027.yaml") -> str:
    """Calculate cryptographic SHA-256 digest of active statutory ruleset YAML."""
    path = settings.rulesets_dir / filename
    if path.exists():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    # Default fallback hash if file is synthetic
    return hashlib.sha256(f"ruleset:{filename}".encode()).hexdigest()


def compute_entry_hash(
    sequence: int,
    prev_hash: str,
    timestamp: str,
    ruleset_hash: str,
    input_digests: list[str],
    model_versions: dict[str, str],
    event_payload: dict[str, Any],
) -> str:
    """Calculate deterministic SHA-256 over canonicalized JSON representation of audit entry."""
    canonical_dict = {
        "sequence": sequence,
        "prev_hash": prev_hash,
        "timestamp": timestamp,
        "ruleset_hash": ruleset_hash,
        "input_digests": sorted(input_digests),
        "model_versions": dict(sorted(model_versions.items())),
        "event_payload": event_payload,
    }
    serialized = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


async def record_evaluation_audit(
    db: AsyncSession,
    dossier: ApplicationDossier,
    findings: list[Finding],
    ruleset_name: str = "aicte_aph_2024_2027.yaml",
    evaluation_id: str | None = None,
) -> AuditLogModel:
    """Record an immutable, hash-chained entry for a completed dossier scrutiny evaluation."""
    eval_id = evaluation_id or f"eval-{uuid.uuid4().hex[:12]}"
    now_ts = datetime.now(UTC).isoformat()

    # Query last audit entry to maintain unbroken chain
    stmt = select(AuditLogModel).order_by(AuditLogModel.sequence.desc()).limit(1)
    res = await db.execute(stmt)
    latest_entry = res.scalar_one_or_none()

    if latest_entry is None:
        sequence = 0
        prev_hash = GENESIS_PREV_HASH
    else:
        sequence = latest_entry.sequence + 1
        prev_hash = latest_entry.entry_hash

    ruleset_digest = get_ruleset_hash(ruleset_name)
    input_digests = sorted([d.forensic.sha256_hash for d in dossier.documents if d.forensic])

    model_versions = {
        "rule_engine": "1.0.0",
        "handbook_edition": settings.active_handbook_edition,
        "yolox": "yolox_m.onnx",
        "ollama_model": settings.ollama_model,
    }

    # Construct complete event payload snapshot
    event_payload: dict[str, Any] = {
        "evaluation_id": eval_id,
        "dossier_id": dossier.dossier_id,
        "institution_name": dossier.institution_name,
        "application_number": dossier.application_number,
        "program": dossier.program,
        "level": dossier.level,
        "institution_type": dossier.institution_type,
        "location_type": dossier.location_type,
        "intake_proposed": dossier.intake_proposed,
        "overall_status": dossier.overall_status.value,
        "risk_score": dossier.risk_score,
        "summary": dossier.summary,
        "documents": [
            {
                "document_id": doc.document_id,
                "doc_type": doc.doc_type.value,
                "file_name": doc.file_name,
                "sha256_hash": doc.forensic.sha256_hash if doc.forensic else "",
                "page_count": doc.page_count,
                "is_self_attested": doc.is_self_attested,
                "is_tampered": doc.forensic.is_tampered if doc.forensic else False,
            }
            for doc in dossier.documents
        ],
        "findings": [
            {
                "finding_id": f.finding_id,
                "rule_id": f.rule_id,
                "rule_name": f.rule_name,
                "category": f.category,
                "status": f.status.value,
                "summary": f.summary,
                "details": f.details,
            }
            for f in findings
        ],
        "extracted_params": getattr(dossier, "extracted_params", {}),
    }

    entry_hash = compute_entry_hash(
        sequence=sequence,
        prev_hash=prev_hash,
        timestamp=now_ts,
        ruleset_hash=ruleset_digest,
        input_digests=input_digests,
        model_versions=model_versions,
        event_payload=event_payload,
    )

    audit_entry = AuditLogModel(
        entry_id=f"audit-{uuid.uuid4().hex[:12]}",
        evaluation_id=eval_id,
        dossier_id=dossier.dossier_id,
        sequence=sequence,
        prev_hash=prev_hash,
        entry_hash=entry_hash,
        timestamp=now_ts,
        ruleset_hash=ruleset_digest,
        input_digests_json=json.dumps(input_digests),
        model_versions_json=json.dumps(model_versions),
        event_payload_json=json.dumps(event_payload),
    )

    db.add(audit_entry)
    await db.commit()
    await db.refresh(audit_entry)
    return audit_entry


def verify_chain(
    entries: list[Any],
) -> ChainVerificationResult:
    """Verify cryptographic integrity of the entire audit hash chain.

    Checks:
    1. Genesis entry starts with sequence 0 and prev_hash == 64 zeroes.
    2. Sequence numbers are strictly monotonic: seq[i] == seq[i-1] + 1.
    3. Each entry's prev_hash exactly equals the prior entry's entry_hash.
    4. Each entry's entry_hash accurately matches the SHA-256 of its payload.
    """
    if not entries:
        return ChainVerificationResult(is_valid=True, total_entries=0)

    for i, entry in enumerate(entries):
        # 1. Sequence check
        if entry.sequence != i:
            return ChainVerificationResult(
                is_valid=False,
                total_entries=len(entries),
                broken_index=i,
                reason=f"Sequence discontinuity at index {i}: found {entry.sequence}, expected {i}",
            )

        # 2. Previous hash link check
        if i == 0:
            if entry.prev_hash != GENESIS_PREV_HASH:
                return ChainVerificationResult(
                    is_valid=False,
                    total_entries=len(entries),
                    broken_index=0,
                    reason=f"Genesis entry prev_hash invalid: found {entry.prev_hash}, expected {GENESIS_PREV_HASH}",
                    expected_hash=GENESIS_PREV_HASH,
                    actual_hash=entry.prev_hash,
                )
        else:
            prev_entry = entries[i - 1]
            if entry.prev_hash != prev_entry.entry_hash:
                return ChainVerificationResult(
                    is_valid=False,
                    total_entries=len(entries),
                    broken_index=i,
                    reason=f"Broken chain link at index {i}: prev_hash does not match previous entry's entry_hash",
                    expected_hash=prev_entry.entry_hash,
                    actual_hash=entry.prev_hash,
                )

        # 3. Payload integrity check
        input_digests = (
            entry.get_input_digests()
            if hasattr(entry, "get_input_digests")
            else getattr(entry, "input_digests", [])
        )
        model_versions = (
            entry.get_model_versions()
            if hasattr(entry, "get_model_versions")
            else getattr(entry, "model_versions", {})
        )
        event_payload = (
            entry.get_event_payload()
            if hasattr(entry, "get_event_payload")
            else getattr(entry, "event_payload", {})
        )

        expected_hash = compute_entry_hash(
            sequence=entry.sequence,
            prev_hash=entry.prev_hash,
            timestamp=entry.timestamp,
            ruleset_hash=entry.ruleset_hash,
            input_digests=input_digests,
            model_versions=model_versions,
            event_payload=event_payload,
        )

        if entry.entry_hash != expected_hash:
            return ChainVerificationResult(
                is_valid=False,
                total_entries=len(entries),
                broken_index=i,
                reason=f"Payload tamper detected at index {i}: entry_hash does not match computed hash",
                expected_hash=expected_hash,
                actual_hash=entry.entry_hash,
            )

    return ChainVerificationResult(
        is_valid=True,
        total_entries=len(entries),
        head_hash=entries[-1].entry_hash,
    )


async def replay(
    evaluation_id: str,
    db: AsyncSession | None = None,
    audit_entry: AuditLogModel | AuditLogEntry | None = None,
) -> ReplayResult:
    """Re-run deterministic scrutiny evaluation from recorded audit state and confirm identical output."""
    entry: AuditLogModel | AuditLogEntry | None = audit_entry

    if entry is None:
        if db is None:
            raise ValueError("Either db session or audit_entry must be provided for replay.")
        stmt = select(AuditLogModel).where(AuditLogModel.evaluation_id == evaluation_id)
        res = await db.execute(stmt)
        entry = res.scalar_one_or_none()
        if not entry:
            raise ValueError(f"Audit log entry for evaluation_id '{evaluation_id}' not found.")

    payload = (
        entry.get_event_payload()
        if hasattr(entry, "get_event_payload")
        else getattr(entry, "event_payload", {})
    )

    # Reconstruct dossier and document models from recorded snapshot
    docs: list[DocumentRecord] = []
    for d_data in payload.get("documents", []):
        forensic = ForensicReport(
            document_id=d_data["document_id"],
            file_name=d_data.get("file_name", "doc.pdf"),
            sha256_hash=d_data.get("sha256_hash", ""),
            file_size_bytes=1024,
            page_count=d_data.get("page_count", 1),
            is_tampered=d_data.get("is_tampered", False),
        )
        docs.append(
            DocumentRecord(
                document_id=d_data["document_id"],
                dossier_id=payload["dossier_id"],
                file_name=d_data.get("file_name", "doc.pdf"),
                doc_type=DocumentType(d_data.get("doc_type", "UNKNOWN")),
                title=d_data.get("file_name", "Doc"),
                page_count=d_data.get("page_count", 1),
                forensic=forensic,
                extracted_text_preview="",
                is_self_attested=d_data.get("is_self_attested", False),
            )
        )

    dossier = ApplicationDossier(
        dossier_id=payload["dossier_id"],
        institution_name=payload["institution_name"],
        application_number=payload["application_number"],
        program=payload["program"],
        level=payload["level"],
        institution_type=payload["institution_type"],
        location_type=payload["location_type"],
        intake_proposed=payload["intake_proposed"],
        documents=docs,
        findings=[],
        overall_status=VerificationStatus(payload["overall_status"]),
        risk_score=payload["risk_score"],
        summary=payload["summary"],
        extracted_params=payload.get("extracted_params", {}),
    )

    # Deterministic rule evaluation
    replayed_extracted_params = payload.get("extracted_params", {})
    replayed_findings = rule_engine.evaluate_dossier(
        dossier, docs, extracted_params=replayed_extracted_params
    )

    # Determine replayed status and risk score identically
    has_tamper = any(f.status == VerificationStatus.FLAGGED_TAMPER for f in replayed_findings)
    has_fail = any(f.status == VerificationStatus.FAIL for f in replayed_findings)
    has_review = any(
        f.status == VerificationStatus.MANUAL_REVIEW_REQUIRED for f in replayed_findings
    )

    if has_tamper:
        replayed_status = VerificationStatus.FLAGGED_TAMPER.value
        replayed_risk_score = 95.0
    elif has_fail:
        replayed_status = VerificationStatus.FAIL.value
        replayed_risk_score = 75.0
    elif has_review:
        replayed_status = VerificationStatus.MANUAL_REVIEW_REQUIRED.value
        replayed_risk_score = 40.0
    else:
        replayed_status = VerificationStatus.PASS.value
        replayed_risk_score = 5.0

    orig_status = payload["overall_status"]
    orig_risk_score = payload["risk_score"]
    orig_findings = payload.get("findings", [])

    diffs: list[str] = []
    if replayed_status != orig_status:
        diffs.append(f"Status mismatch: recorded '{orig_status}' vs replayed '{replayed_status}'")
    if abs(replayed_risk_score - orig_risk_score) > 0.01:
        diffs.append(
            f"Risk score mismatch: recorded {orig_risk_score} vs replayed {replayed_risk_score}"
        )
    if len(replayed_findings) != len(orig_findings):
        diffs.append(
            f"Findings count mismatch: recorded {len(orig_findings)} vs replayed {len(replayed_findings)}"
        )

    return ReplayResult(
        evaluation_id=evaluation_id,
        is_identical=len(diffs) == 0,
        original_status=orig_status,
        replayed_status=replayed_status,
        original_risk_score=orig_risk_score,
        replayed_risk_score=replayed_risk_score,
        original_findings_count=len(orig_findings),
        replayed_findings_count=len(replayed_findings),
        diffs=diffs,
    )
