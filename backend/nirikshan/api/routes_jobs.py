"""API routes for asynchronous verification jobs and SSE stage-by-stage event streaming."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nirikshan.db.models import DossierModel, JobModel
from nirikshan.db.session import get_db
from nirikshan.worker.job_service import broadcaster, execute_verification_job

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class JobResponse(BaseModel):
    job_id: str
    dossier_id: str
    status: str
    current_stage: str
    progress_percent: int
    stage_message: str
    result: dict[str, Any] | None = None
    error_message: str | None = None


@router.post("/dossiers/{dossier_id}/evaluate", response_model=JobResponse)
async def submit_evaluation_job(
    dossier_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Submit an asynchronous scrutiny job for a dossier with stage-by-stage event tracking."""
    stmt = select(DossierModel).where(DossierModel.dossier_id == dossier_id)
    res = await db.execute(stmt)
    dossier = res.scalar_one_or_none()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")

    job_id = f"job-{uuid.uuid4().hex[:10]}"
    job = JobModel(
        job_id=job_id,
        dossier_id=dossier_id,
        status="PENDING",
        current_stage="ingest",
        progress_percent=0,
        stage_message="Job queued for asynchronous scrutiny evaluation.",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Launch background worker task
    background_tasks.add_task(execute_verification_job, job_id, dossier_id)

    return JobResponse(
        job_id=job.job_id,
        dossier_id=job.dossier_id,
        status=job.status,
        current_stage=job.current_stage,
        progress_percent=job.progress_percent,
        stage_message=job.stage_message,
        result=job.get_result(),
        error_message=job.error_message,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Retrieve the current processing state and progress percent of a verification job."""
    stmt = select(JobModel).where(JobModel.job_id == job_id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(
        job_id=job.job_id,
        dossier_id=job.dossier_id,
        status=job.status,
        current_stage=job.current_stage,
        progress_percent=job.progress_percent,
        stage_message=job.stage_message,
        result=job.get_result(),
        error_message=job.error_message,
    )


@router.get("/{job_id}/events")
async def stream_job_events(
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream stage-by-stage progress events (ingest, ocr, forensics, crypto, extract, rules, graph) via SSE."""
    stmt = select(JobModel).where(JobModel.job_id == job_id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator() -> AsyncIterator[str]:
        # Initial comment / keepalive
        yield ": nirikshan-sse-connected\n\n"
        async for event in broadcaster.subscribe(job_id):
            yield event.to_sse_message()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
