"""API routes for scrutiny reports and trust ladder radar."""

import json
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from nirikshan.db.models import DossierModel
from nirikshan.db.session import get_db
from nirikshan.trust.ladder import TRUST_RANKS, TrustLevel

router = APIRouter(prefix="/api/dossiers/{dossier_id}/report", tags=["reports"])


@router.get("", response_model=dict[str, Any])
async def generate_scrutiny_report(
    dossier_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate comprehensive, explainable AICTE regulatory scrutiny report.

    Contains full Trust Ladder breakdown, rule citations, evidence items, and bounding boxes.
    """
    stmt = (
        select(DossierModel)
        .options(selectinload(DossierModel.documents), selectinload(DossierModel.findings))
        .where(DossierModel.dossier_id == dossier_id)
    )
    res = await db.execute(stmt)
    dossier = res.scalar_one_or_none()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")

    # Trust Ladder Distribution
    trust_distribution: dict[str, int] = {level.value: 0 for level in TrustLevel}
    findings_summary: dict[str, int] = {
        "PASS": 0,
        "FAIL": 0,
        "MANUAL_REVIEW": 0,
        "FLAGGED_TAMPER": 0,
    }

    findings_list = []
    for f in dossier.findings:
        citation = json.loads(f.handbook_citation_json) if f.handbook_citation_json else {}
        evidence_items = json.loads(f.evidence_list_json) if f.evidence_list_json else []
        bbox = json.loads(f.bounding_box_json) if f.bounding_box_json else None
        advisory_notes = json.loads(f.advisory_notes_json) if f.advisory_notes_json else []

        for ev in evidence_items:
            t_level = ev.get("trust_level", TrustLevel.UNVERIFIED_CLAIM.value)
            if t_level in trust_distribution:
                trust_distribution[t_level] += 1

        if f.status == "PASS":
            findings_summary["PASS"] += 1
        elif f.status == "FAIL":
            findings_summary["FAIL"] += 1
        elif f.status == "FLAGGED_TAMPER":
            findings_summary["FLAGGED_TAMPER"] += 1
        else:
            findings_summary["MANUAL_REVIEW"] += 1

        findings_list.append(
            {
                "finding_id": f.finding_id,
                "rule_id": f.rule_id,
                "rule_name": f.rule_name,
                "category": f.category,
                "status": f.status,
                "summary": f.summary,
                "details": f.details,
                "handbook_citation": citation,
                "evidence_count": len(evidence_items),
                "evidence_list": evidence_items,
                "primary_bounding_box": bbox,
                "advisory_notes": advisory_notes,
                "is_model_advisory_only": f.is_model_advisory_only,
                "needs_verification": f.needs_verification,
            }
        )

    return {
        "report_id": f"rep-{dossier_id}",
        "generated_at": datetime.now(UTC).isoformat(),
        "regulatory_standard": "AICTE Approval Process Handbook (APH 2024-2027)",
        "dossier": {
            "dossier_id": dossier.dossier_id,
            "institution_name": dossier.institution_name,
            "application_number": dossier.application_number,
            "program": dossier.program,
            "level": dossier.level,
            "institution_type": dossier.institution_type,
            "location_type": dossier.location_type,
            "intake_proposed": dossier.intake_proposed,
            "overall_status": dossier.overall_status,
            "risk_score": dossier.risk_score,
            "summary": dossier.summary,
            "document_count": len(dossier.documents),
        },
        "findings_metrics": findings_summary,
        "trust_ladder_distribution": trust_distribution,
        "trust_ladder_ranks": {k.value: v for k, v in TRUST_RANKS.items()},
        "findings": findings_list,
        "tamper_alerts": [
            {
                "document_id": d.document_id,
                "file_name": d.file_name,
                "is_tampered": d.is_tampered,
                "forensic": json.loads(d.forensic_json) if d.forensic_json else {},
            }
            for d in dossier.documents
            if d.is_tampered
        ],
    }
