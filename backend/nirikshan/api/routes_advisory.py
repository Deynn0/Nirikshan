"""FastAPI routes for Advisory ML Layer (Trust Ladder: MODEL).

All endpoints here emit advisory outputs only and cannot independently issue PASS or FAIL.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import aiofiles
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from nirikshan.advisory.ask_why import (
    AskWhyContext,
    AskWhyResponse,
    ask_why_assistant,
)
from nirikshan.advisory.asset_counter import (
    LabInventoryResult,
    MockLabAssetDetector,
    YOLOXAssetDetector,
    verify_lab_inventory,
)
from nirikshan.advisory.extractor import StubFieldExtractor
from nirikshan.advisory.grounding import (
    GroundedResult,
    RecognizedDocument,
    grounded_verifier,
)
from nirikshan.config import settings

router = APIRouter(prefix="/api/advisory", tags=["advisory-ml"])


class ExtractAndGroundRequest(BaseModel):
    """Request payload for text field extraction and grounding."""

    text: str = Field(..., description="Raw text or OCR output")
    schema_definition: dict[str, Any] | None = Field(default=None, description="Optional target JSON schema")
    pages_text: list[str] | None = Field(default=None, description="Optional page-split text for spatial tokens")


class AskWhyRequest(BaseModel):
    """Request payload for Ask Why officer assistant."""

    question: str
    finding: dict[str, Any] | None = None
    rule: dict[str, Any] | None = None
    facts: dict[str, Any] = Field(default_factory=dict)
    evidence_items: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/extract", response_model=GroundedResult)
async def extract_and_ground(request: ExtractAndGroundRequest) -> GroundedResult:
    """Extract structured fields using Ollama/Stub and verify grounding with spatial bboxes."""
    extractor = StubFieldExtractor()
    extracted = extractor.extract(text=request.text, schema=request.schema_definition)

    # Build recognized document representation
    pages = request.pages_text or [request.text]
    rec_doc = RecognizedDocument.from_text_pages(pages)

    # Grounded verification: discard ungrounded hallucinations
    return grounded_verifier.verify_and_ground(extracted, rec_doc)


@router.post("/asset-count", response_model=LabInventoryResult)
async def audit_lab_assets(
    file: UploadFile = File(...),
    declared_count: int = Form(...),
    rule_id: str = Form(default="AICTE-2024-LAB-001"),
    use_mock: bool = Form(default=True),
) -> LabInventoryResult:
    """Detect workstations in a lab photo, compare with declared inventory, and emit advisory Finding."""
    file_ext = Path(file.filename or "photo.jpg").suffix or ".jpg"
    temp_filename = f"lab_upload_{uuid.uuid4().hex[:8]}{file_ext}"
    temp_path = settings.quarantine_dir / temp_filename

    async with aiofiles.open(temp_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    detector = MockLabAssetDetector(mock_count=20) if use_mock or not settings.yolox_model_path.exists() else YOLOXAssetDetector()

    try:
        return verify_lab_inventory(
            image_path=temp_path,
            declared_count=declared_count,
            detector=detector,
            rule_id=rule_id,
            document_id=f"doc-lab-{uuid.uuid4().hex[:8]}",
            document_name=file.filename or "lab_photo.jpg",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Asset detection failed: {exc}") from exc


@router.post("/ask-why", response_model=AskWhyResponse)
async def ask_why(request: AskWhyRequest) -> AskWhyResponse:
    """Answer scrutiny officer questions using strictly grounded context with citations."""
    import contextlib

    from nirikshan.schemas.finding import Finding
    from nirikshan.trust.ladder import EvidenceItem

    finding_obj: Finding | None = None
    if request.finding:
        with contextlib.suppress(Exception):
            finding_obj = Finding.model_validate(request.finding)

    evidence_objs: list[EvidenceItem] = []
    for ev in request.evidence_items:
        with contextlib.suppress(Exception):
            evidence_objs.append(EvidenceItem.model_validate(ev))

    context = AskWhyContext(
        finding=finding_obj,
        rule=request.rule,
        facts=request.facts,
        evidence_items=evidence_objs,
    )

    return ask_why_assistant.ask(question=request.question, context=context)
