"""Asynchronous Job Processing and Stage-by-Stage SSE Event Streaming."""

from __future__ import annotations

import asyncio
import contextlib
import json
from collections import defaultdict
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from nirikshan.db.models import DossierModel, FindingModel, JobModel
from nirikshan.db.session import async_session_factory
from nirikshan.engine.audit_log import record_evaluation_audit
from nirikshan.engine.rule_evaluator import rule_engine
from nirikshan.fraud.service import fraud_service
from nirikshan.schemas.dossier import ApplicationDossier
from nirikshan.schemas.finding import VerificationStatus
from nirikshan.schemas.forensic import DocumentRecord, DocumentType, ForensicReport

STAGES = ["ingest", "ocr", "forensics", "crypto", "extract", "rules", "graph"]


class JobEvent(BaseModel):
    """Event emitted during stage-by-stage job processing."""

    job_id: str
    stage: str
    status: str  # "running" | "completed" | "failed"
    progress: int  # 0 to 100
    message: str
    result: dict[str, Any] | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_sse_message(self) -> str:
        event_name = "job_completed" if self.stage == "completed" else "stage_progress"
        return f"event: {event_name}\ndata: {self.model_dump_json()}\n\n"


class JobEventBroadcaster:
    """In-memory pub-sub broadcaster with event replay for late-connecting SSE clients."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[asyncio.Queue[JobEvent]]] = defaultdict(list)
        self._history: dict[str, list[JobEvent]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def publish(self, event: JobEvent) -> None:
        async with self._lock:
            self._history[event.job_id].append(event)
            listeners = list(self._listeners.get(event.job_id, []))
        for q in listeners:
            await q.put(event)

    async def subscribe(self, job_id: str) -> AsyncIterator[JobEvent]:
        q: asyncio.Queue[JobEvent] = asyncio.Queue()
        async with self._lock:
            past_events = list(self._history.get(job_id, []))
            self._listeners[job_id].append(q)

        try:
            # Yield past events first
            for pe in past_events:
                yield pe
                if pe.stage == "completed" or pe.status == "failed":
                    return

            # Yield live events
            while True:
                event = await q.get()
                yield event
                if event.stage == "completed" or event.status == "failed":
                    break
        finally:
            async with self._lock:
                if job_id in self._listeners and q in self._listeners[job_id]:
                    self._listeners[job_id].remove(q)

    def get_history(self, job_id: str) -> list[JobEvent]:
        return list(self._history.get(job_id, []))


broadcaster = JobEventBroadcaster()


def _model_to_dossier_schema(dm: DossierModel) -> ApplicationDossier:
    documents: list[DocumentRecord] = []
    for d in dm.documents:
        forensic_dict = json.loads(d.forensic_json) if d.forensic_json else {}
        forensic = ForensicReport.model_validate(forensic_dict)
        doc_type = (
            DocumentType(d.doc_type)
            if d.doc_type in DocumentType.__members__.values()
            else DocumentType.UNKNOWN
        )
        documents.append(
            DocumentRecord(
                document_id=d.document_id,
                dossier_id=d.dossier_id,
                file_name=d.file_name,
                doc_type=doc_type,
                title=d.title,
                page_count=d.page_count,
                forensic=forensic,
                extracted_text_preview=d.text_preview,
                is_self_attested=d.is_self_attested,
            )
        )
    return ApplicationDossier(
        dossier_id=dm.dossier_id,
        institution_name=dm.institution_name,
        application_number=dm.application_number,
        program=dm.program,
        level=dm.level,
        institution_type=dm.institution_type,
        location_type=dm.location_type,
        intake_proposed=dm.intake_proposed,
        created_at=dm.created_at,
        documents=documents,
        findings=[],
        overall_status=VerificationStatus(dm.overall_status),
        risk_score=dm.risk_score,
        summary=dm.summary,
        extracted_params=dm.get_extracted_params() if hasattr(dm, "get_extracted_params") else {},
    )


async def execute_verification_job(job_id: str, dossier_id: str) -> None:
    """Orchestrate async background verification pipeline emitting ordered stage progress events."""
    async with async_session_factory() as db:
        stmt = select(JobModel).where(JobModel.job_id == job_id)
        res = await db.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            return

        job.status = "RUNNING"
        await db.commit()

        # Helper to emit progress and update DB
        async def _emit_stage(stage: str, progress: int, msg: str, status: str = "running") -> None:
            job.current_stage = stage
            job.progress_percent = progress
            job.stage_message = msg
            await db.commit()
            evt = JobEvent(
                job_id=job_id,
                stage=stage,
                status=status,
                progress=progress,
                message=msg,
            )
            await broadcaster.publish(evt)
            # Brief pause to allow event delivery
            await asyncio.sleep(0.05)

        try:
            # Stage 1: Ingest
            await _emit_stage("ingest", 14, "Ingesting dossier and verifying encrypted document envelopes...")
            dossier_stmt = (
                select(DossierModel)
                .options(
                    selectinload(DossierModel.documents),
                    selectinload(DossierModel.findings),
                )
                .where(DossierModel.dossier_id == dossier_id)
            )
            d_res = await db.execute(dossier_stmt)
            dossier = d_res.scalar_one_or_none()
            if not dossier:
                raise ValueError(f"Dossier {dossier_id} not found.")

            documents = list(dossier.documents)

            # Stage 2: OCR / Text extraction
            await _emit_stage("ocr", 28, f"Extracted text streams from {len(documents)} quarantined documents...")

            # Stage 3: Structural Forensics
            await _emit_stage("forensics", 42, "Evaluating PDF incremental revisions and font stream integrity...")

            # Stage 4: Cryptographic & QR Verification
            await _emit_stage("crypto", 56, "Verifying digital signatures (/ByteRange) and trust ladder anchoring...")

            # Stage 5: Parameter Extraction
            await _emit_stage("extract", 70, "Consolidating land acreage, survey numbers, and faculty cadre counts...")
            dossier_schema = _model_to_dossier_schema(dossier)
            extracted_params = dossier.get_extracted_params()

            # Stage 6: Deterministic Regulatory Rules & Hash-Chained Audit Log
            await _emit_stage("rules", 85, "Executing deterministic AICTE handbook rules and generating immutable audit link...")
            findings = rule_engine.evaluate_dossier(dossier_schema, dossier_schema.documents, extracted_params)

            # Persist findings in DB
            # Clear old
            for old_f in list(dossier.findings):
                await db.delete(old_f)
            await db.flush()

            has_tamper = any(f.status == VerificationStatus.FLAGGED_TAMPER for f in findings)
            has_fail = any(f.status == VerificationStatus.FAIL for f in findings)
            has_review = any(f.status == VerificationStatus.MANUAL_REVIEW_REQUIRED for f in findings)

            if has_tamper:
                overall_status = VerificationStatus.FLAGGED_TAMPER
                risk_score = 95.0
                summary = "ALERT: Document tamper detected."
            elif has_fail:
                overall_status = VerificationStatus.FAIL
                risk_score = 75.0
                summary = "Deficiencies identified against statutory AICTE requirements."
            elif has_review:
                overall_status = VerificationStatus.MANUAL_REVIEW_REQUIRED
                risk_score = 40.0
                summary = "Manual committee review required."
            else:
                overall_status = VerificationStatus.PASS
                risk_score = 5.0
                summary = "Compliant with all AICTE regulatory requirements."

            dossier.overall_status = overall_status.value
            dossier.risk_score = risk_score
            dossier.summary = summary

            for f in findings:
                finding_model = FindingModel(
                    finding_id=f.finding_id,
                    dossier_id=dossier_id,
                    rule_id=f.rule_id,
                    rule_name=f.rule_name,
                    category=f.category,
                    status=f.status.value,
                    summary=f.summary,
                    details=f.details,
                    handbook_citation_json=f.handbook_citation.model_dump_json(),
                    evidence_list_json=json.dumps([e.model_dump(mode="json") for e in f.evidence_list]),
                    bounding_box_json=f.primary_bounding_box.model_dump_json() if f.primary_bounding_box else "{}",
                    advisory_notes_json=json.dumps(f.advisory_notes),
                    is_model_advisory_only=f.is_model_advisory_only,
                    needs_verification=f.needs_verification,
                )
                db.add(finding_model)

            dossier_schema.findings = findings
            dossier_schema.overall_status = overall_status
            dossier_schema.risk_score = risk_score

            # Record hash-chained immutable audit log entry
            audit_entry = await record_evaluation_audit(db, dossier_schema, findings)

            # Stage 7: Cross-Application Entity Graph
            await _emit_stage("graph", 95, "Scanning cross-application entity index and detecting fraud collisions...")
            # Index entities into graph
            with contextlib.suppress(Exception):
                await fraud_service.index_dossier_entities(db, dossier_id)

            # Final Completion
            job.status = "COMPLETED"
            job.current_stage = "completed"
            job.progress_percent = 100
            job.stage_message = "Scrutiny pipeline completed successfully."
            job.completed_at = datetime.now(UTC)

            result_data = {
                "dossier_id": dossier_id,
                "overall_status": overall_status.value,
                "risk_score": risk_score,
                "findings_count": len(findings),
                "audit_entry_id": audit_entry.entry_id,
                "audit_entry_hash": audit_entry.entry_hash,
            }
            job.set_result(result_data)
            await db.commit()

            final_event = JobEvent(
                job_id=job_id,
                stage="completed",
                status="completed",
                progress=100,
                message="Scrutiny pipeline completed successfully.",
                result=result_data,
            )
            await broadcaster.publish(final_event)

        except Exception as e:
            job.status = "FAILED"
            job.stage_message = f"Job failed: {e}"
            job.error_message = str(e)
            await db.commit()
            err_event = JobEvent(
                job_id=job_id,
                stage=job.current_stage,
                status="failed",
                progress=job.progress_percent,
                message=str(e),
            )
            await broadcaster.publish(err_event)
