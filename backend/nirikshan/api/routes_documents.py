"""API routes for uploading and inspecting documents."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nirikshan.crypto.storage import encrypted_storage
from nirikshan.db.models import DocumentModel, DossierModel
from nirikshan.db.session import get_db
from nirikshan.sandbox import SandboxedWorkerError, worker_manager
from nirikshan.schemas.forensic import DocumentRecord, DocumentType

router = APIRouter(prefix="/api/dossiers/{dossier_id}/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentRecord)
async def upload_document(
    dossier_id: str,
    file: UploadFile = File(...),
    doc_type: str = Form(default="LAND_SALE_DEED"),
    title: str = Form(default=""),
    is_self_attested: bool = Form(default=False),
    land_area_acres: float | None = Form(default=None),
    survey_no: str | None = Form(default=None),
    faculty_count: int | None = Form(default=None),
    cadre_professors: int | None = Form(default=None),
    cadre_assoc_professors: int | None = Form(default=None),
    cadre_asst_professors: int | None = Form(default=None),
    fdr_amount_lakhs: float | None = Form(default=None),
    built_up_area_sqm: float | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
) -> DocumentRecord:
    """Safely receive an untrusted regulatory document.

    Stores in quarantine and delegates parsing exclusively to the isolated sandboxed worker.
    """
    stmt = select(DossierModel).where(DossierModel.dossier_id == dossier_id)
    res = await db.execute(stmt)
    dossier = res.scalar_one_or_none()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")

    document_id = f"doc-{uuid.uuid4().hex[:8]}"
    content = await file.read()

    # Store with envelope encryption: AES-256-GCM data key wrapped by master key
    quarantine_path, envelope = encrypted_storage.store_document(document_id, content)

    # Untrusted files are parsed only inside the sandboxed worker (transparent decrypt in sandbox)
    try:
        forensic, text_preview, extracted_params = worker_manager.parse_document_isolated(
            quarantine_path, document_id
        )
    except SandboxedWorkerError as e:
        raise HTTPException(status_code=422, detail=f"Sandboxed parsing failed: {e!s}") from e

    # Merge user-supplied form fields into dossier extracted parameters
    dossier_params = dossier.get_extracted_params()
    if land_area_acres is not None:
        dossier_params["land_area_acres"] = land_area_acres
    elif "land_area_acres" in extracted_params:
        dossier_params["land_area_acres"] = extracted_params["land_area_acres"]

    if survey_no:
        if doc_type in ("LAND_SALE_DEED", "LAND_LEASE_DEED"):
            dossier_params["survey_no_deed"] = survey_no
        elif doc_type == "LAND_USE_CONVERSION_CERT":
            dossier_params["survey_no_conversion"] = survey_no
        elif doc_type == "BUILDING_PLAN_APPROVED":
            dossier_params["survey_no_building_plan"] = survey_no

    if faculty_count is not None:
        dossier_params["faculty_count"] = faculty_count
    if cadre_professors is not None:
        dossier_params["cadre_professors"] = cadre_professors
    if cadre_assoc_professors is not None:
        dossier_params["cadre_assoc_professors"] = cadre_assoc_professors
    if cadre_asst_professors is not None:
        dossier_params["cadre_asst_professors"] = cadre_asst_professors
    if fdr_amount_lakhs is not None:
        dossier_params["fdr_amount_lakhs"] = fdr_amount_lakhs
    if built_up_area_sqm is not None:
        dossier_params["built_up_area_sqm"] = built_up_area_sqm

    dossier.set_extracted_params(dossier_params)

    # Normalize DocumentType
    dt_enum = (
        DocumentType(doc_type)
        if doc_type in DocumentType.__members__.values()
        else DocumentType.UNKNOWN
    )

    doc_model = DocumentModel(
        document_id=document_id,
        dossier_id=dossier_id,
        file_name=file.filename or quarantine_path.name,
        doc_type=dt_enum.value,
        title=title or (file.filename or "Regulatory Document"),
        quarantine_path=str(quarantine_path),
        page_count=forensic.page_count,
        sha256_hash=forensic.sha256_hash,
        is_self_attested=is_self_attested or (dt_enum == DocumentType.AFFIDAVIT_SELF_DECLARATION),
        is_tampered=forensic.is_tampered,
        forensic_json=forensic.model_dump_json(),
        text_preview=text_preview,
    )

    db.add(doc_model)
    await db.commit()
    await db.refresh(doc_model)

    return DocumentRecord(
        document_id=doc_model.document_id,
        dossier_id=doc_model.dossier_id,
        file_name=doc_model.file_name,
        doc_type=dt_enum,
        title=doc_model.title,
        page_count=doc_model.page_count,
        forensic=forensic,
        extracted_text_preview=doc_model.text_preview,
        is_self_attested=doc_model.is_self_attested,
    )


@router.get("/{document_id}/file")
async def get_document_file(
    dossier_id: str,
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Serve quarantined document file for scrutiny preview and bounding-box overlay."""
    stmt = select(DocumentModel).where(
        DocumentModel.dossier_id == dossier_id, DocumentModel.document_id == document_id
    )
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = Path(doc.quarantine_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Quarantined file missing from disk")

    return FileResponse(
        path=file_path,
        media_type="application/pdf"
        if file_path.suffix.lower() == ".pdf"
        else "application/octet-stream",
        filename=doc.file_name,
    )
