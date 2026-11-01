"""API routes for audit log verification and deterministic evaluation replay."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nirikshan.db.models import AuditLogModel
from nirikshan.db.session import get_db
from nirikshan.engine.audit_log import (
    ChainVerificationResult,
    ReplayResult,
    replay,
    verify_chain,
)

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/chain", response_model=ChainVerificationResult)
async def get_audit_chain_status(
    db: AsyncSession = Depends(get_db),
) -> ChainVerificationResult:
    """Verify cryptographic integrity of the immutable audit hash chain."""
    stmt = select(AuditLogModel).order_by(AuditLogModel.sequence.asc())
    res = await db.execute(stmt)
    entries = list(res.scalars().all())
    return verify_chain(entries)


@router.get("/entries")
async def list_audit_entries(
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List all audit log entries with previous hash and entry hash."""
    stmt = select(AuditLogModel).order_by(AuditLogModel.sequence.asc())
    res = await db.execute(stmt)
    entries = res.scalars().all()
    return [
        {
            "entry_id": e.entry_id,
            "evaluation_id": e.evaluation_id,
            "dossier_id": e.dossier_id,
            "sequence": e.sequence,
            "prev_hash": e.prev_hash,
            "entry_hash": e.entry_hash,
            "timestamp": e.timestamp,
            "ruleset_hash": e.ruleset_hash,
            "input_digests": e.get_input_digests(),
            "model_versions": e.get_model_versions(),
        }
        for e in entries
    ]


@router.post("/replay/{evaluation_id}", response_model=ReplayResult)
async def replay_evaluation_endpoint(
    evaluation_id: str,
    db: AsyncSession = Depends(get_db),
) -> ReplayResult:
    """Replay recorded evaluation and confirm identical deterministic output."""
    try:
        return await replay(evaluation_id=evaluation_id, db=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
