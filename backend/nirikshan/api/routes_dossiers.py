"""API routes for institutional application dossiers."""

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from nirikshan.db.models import DossierModel, FindingModel
from nirikshan.db.session import get_db
from nirikshan.engine.audit_log import record_evaluation_audit
from nirikshan.engine.rule_evaluator import rule_engine
from nirikshan.schemas.citation import HandbookCitation
from nirikshan.schemas.dossier import ApplicationDossier, DossierCreate
from nirikshan.schemas.finding import Finding, VerificationStatus
from nirikshan.schemas.forensic import DocumentRecord, DocumentType, ForensicReport
from nirikshan.trust.ladder import BoundingBox, EvidenceItem

router = APIRouter(prefix="/api/dossiers", tags=["dossiers"])


def _model_to_schema(dm: DossierModel) -> ApplicationDossier:
    """Convert DB model to Pydantic schema."""
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

    findings: list[Finding] = []
    for f in dm.findings:
        citation_dict = json.loads(f.handbook_citation_json) if f.handbook_citation_json else {}
        citation = HandbookCitation.model_validate(citation_dict)

        ev_list_data = json.loads(f.evidence_list_json) if f.evidence_list_json else []
        evidence_list = [EvidenceItem.model_validate(item) for item in ev_list_data]

        bbox_data = json.loads(f.bounding_box_json) if f.bounding_box_json else None
        bbox = BoundingBox.model_validate(bbox_data) if bbox_data else None

        advisory_notes = json.loads(f.advisory_notes_json) if f.advisory_notes_json else []

        findings.append(
            Finding(
                finding_id=f.finding_id,
                rule_id=f.rule_id,
                rule_name=f.rule_name,
                category=f.category,
                status=VerificationStatus(f.status),
                summary=f.summary,
                details=f.details,
                handbook_citation=citation,
                evidence_list=evidence_list,
                primary_bounding_box=bbox,
                advisory_notes=advisory_notes,
                is_model_advisory_only=f.is_model_advisory_only,
                needs_verification=f.needs_verification,
                timestamp=f.created_at,
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
        findings=findings,
        overall_status=VerificationStatus(dm.overall_status),
        risk_score=dm.risk_score,
        summary=dm.summary,
        extracted_params=dm.get_extracted_params() if hasattr(dm, "get_extracted_params") else {},
    )


@router.post("", response_model=ApplicationDossier)
async def create_dossier(
    payload: DossierCreate,
    db: AsyncSession = Depends(get_db),
) -> ApplicationDossier:
    """Register a new institution application dossier for scrutiny."""
    dossier_id = f"dos-{uuid.uuid4().hex[:10]}"
    dossier = DossierModel(
        dossier_id=dossier_id,
        institution_name=payload.institution_name,
        application_number=payload.application_number,
        program=payload.program,
        level=payload.level,
        institution_type=payload.institution_type,
        location_type=payload.location_type,
        intake_proposed=payload.intake_proposed,
        overall_status=VerificationStatus.INCONCLUSIVE.value,
        risk_score=0.0,
        summary="Dossier registered. Documents pending verification.",
    )
    db.add(dossier)
    await db.commit()
    await db.refresh(dossier)

    # Re-fetch with relationships loaded
    stmt = (
        select(DossierModel)
        .options(selectinload(DossierModel.documents), selectinload(DossierModel.findings))
        .where(DossierModel.dossier_id == dossier_id)
    )
    res = await db.execute(stmt)
    loaded = res.scalar_one()
    return _model_to_schema(loaded)


@router.get("", response_model=list[ApplicationDossier])
async def list_dossiers(
    db: AsyncSession = Depends(get_db),
) -> list[ApplicationDossier]:
    """List all application dossiers."""
    stmt = (
        select(DossierModel)
        .options(selectinload(DossierModel.documents), selectinload(DossierModel.findings))
        .order_by(DossierModel.created_at.desc())
    )
    res = await db.execute(stmt)
    dossiers = res.scalars().all()
    return [_model_to_schema(d) for d in dossiers]


@router.get("/{dossier_id}", response_model=ApplicationDossier)
async def get_dossier(
    dossier_id: str,
    db: AsyncSession = Depends(get_db),
) -> ApplicationDossier:
    """Retrieve full details, documents, and verification findings of a dossier."""
    stmt = (
        select(DossierModel)
        .options(selectinload(DossierModel.documents), selectinload(DossierModel.findings))
        .where(DossierModel.dossier_id == dossier_id)
    )
    res = await db.execute(stmt)
    dossier = res.scalar_one_or_none()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")
    return _model_to_schema(dossier)


@router.post("/{dossier_id}/verify", response_model=ApplicationDossier)
async def verify_dossier(
    dossier_id: str,
    db: AsyncSession = Depends(get_db),
) -> ApplicationDossier:
    """Execute offline deterministic scrutiny engine over the dossier's uploaded documents."""
    stmt = (
        select(DossierModel)
        .options(selectinload(DossierModel.documents), selectinload(DossierModel.findings))
        .where(DossierModel.dossier_id == dossier_id)
    )
    res = await db.execute(stmt)
    dossier = res.scalar_one_or_none()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")

    dossier_schema = _model_to_schema(dossier)
    extracted_params = dossier.get_extracted_params()

    # Accumulate params from all documents
    for doc in dossier_schema.documents:
        # If parameters were extracted during parsing
        if doc.forensic.is_tampered:
            extracted_params["has_tamper_flag"] = True

    # Run deterministic rule engine
    findings = rule_engine.evaluate_dossier(
        dossier_schema, dossier_schema.documents, extracted_params
    )

    # Clear old findings
    for old_f in list(dossier.findings):
        await db.delete(old_f)
    await db.flush()

    # Determine overall status and risk score
    has_tamper = any(f.status == VerificationStatus.FLAGGED_TAMPER for f in findings)
    has_fail = any(f.status == VerificationStatus.FAIL for f in findings)
    has_review = any(f.status == VerificationStatus.MANUAL_REVIEW_REQUIRED for f in findings)

    if has_tamper:
        overall_status = VerificationStatus.FLAGGED_TAMPER
        risk_score = 95.0
        summary = "ALERT: Document tamper or structural anomaly detected. Committee investigation recommended."
    elif has_fail:
        overall_status = VerificationStatus.FAIL
        risk_score = 75.0
        summary = "Deficiencies identified against AICTE APH 2024-2027 statutory requirements."
    elif has_review:
        overall_status = VerificationStatus.MANUAL_REVIEW_REQUIRED
        risk_score = 40.0
        summary = "Self-attestations or model outputs require manual committee scrutiny."
    else:
        overall_status = VerificationStatus.PASS
        risk_score = 5.0
        summary = "Compliant: All AICTE statutory criteria verified by deterministic rules."

    dossier.overall_status = overall_status.value
    dossier.risk_score = risk_score
    dossier.summary = summary

    # Persist new findings
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
            bounding_box_json=f.primary_bounding_box.model_dump_json()
            if f.primary_bounding_box
            else "{}",
            advisory_notes_json=json.dumps(f.advisory_notes),
            is_model_advisory_only=f.is_model_advisory_only,
            needs_verification=f.needs_verification,
        )
        db.add(finding_model)

    await db.commit()
    db.expire_all()

    # Re-fetch with new findings
    res = await db.execute(stmt)
    updated = res.scalar_one()
    updated_schema = _model_to_schema(updated)

    # Cryptographically record audit log entry
    await record_evaluation_audit(db, updated_schema, findings)

    return updated_schema
