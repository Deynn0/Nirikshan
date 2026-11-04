"""System Integrity, Security & Audit Trail: Event sourcing, immutable audit log verification."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient

from nirikshan.db.models import DossierModel
from nirikshan.db.session import async_session_factory, init_db
from nirikshan.engine.audit_log import (
    AuditLogEntry,
    compute_entry_hash,
    record_evaluation_audit,
    replay,
    verify_chain,
)
from nirikshan.engine.rule_evaluator import rule_engine
from nirikshan.main import app
from nirikshan.schemas.dossier import ApplicationDossier
from nirikshan.schemas.finding import VerificationStatus
from nirikshan.worker.job_service import broadcaster


@pytest.fixture(autouse=True)
async def _setup_database() -> None:
    await init_db()


def test_audit_chain_valid_progression() -> None:
    """Sequential construction and hash verification of immutable audit ledger."""
    entries: list[AuditLogEntry] = []
    prev = "0" * 64

    for seq in range(4):
        now_ts = datetime.now(UTC).isoformat()
        payload = {"step": seq, "status": "PASS", "score": 90.0}
        entry_hash = compute_entry_hash(
            sequence=seq,
            prev_hash=prev,
            timestamp=now_ts,
            ruleset_hash="ruleset-sha256",
            input_digests=["doc-hash-1"],
            model_versions={"rule_engine": "1.0"},
            event_payload=payload,
        )
        entry = AuditLogEntry(
            entry_id=f"audit-{seq}",
            evaluation_id=f"eval-{seq}",
            dossier_id=f"dos-{seq}",
            sequence=seq,
            prev_hash=prev,
            entry_hash=entry_hash,
            timestamp=now_ts,
            ruleset_hash="ruleset-sha256",
            input_digests=["doc-hash-1"],
            model_versions={"rule_engine": "1.0"},
            event_payload=payload,
        )
        entries.append(entry)
        prev = entry_hash

    res = verify_chain(entries)
    assert res.is_valid is True
    assert res.total_entries == 4
    assert res.head_hash == entries[-1].entry_hash


def test_audit_chain_tamper_detection() -> None:
    """Altering prev_hash or event payload breaks the cryptographic chain at exact index."""
    entries: list[AuditLogEntry] = []
    prev = "0" * 64

    for seq in range(3):
        now_ts = datetime.now(UTC).isoformat()
        payload = {"step": seq, "val": 100}
        ehash = compute_entry_hash(
            sequence=seq,
            prev_hash=prev,
            timestamp=now_ts,
            ruleset_hash="rules-hash",
            input_digests=[],
            model_versions={},
            event_payload=payload,
        )
        entries.append(
            AuditLogEntry(
                entry_id=f"audit-{seq}",
                evaluation_id=f"eval-{seq}",
                dossier_id="dos-1",
                sequence=seq,
                prev_hash=prev,
                entry_hash=ehash,
                timestamp=now_ts,
                ruleset_hash="rules-hash",
                input_digests=[],
                model_versions={},
                event_payload=payload,
            )
        )
        prev = ehash

    # 1. Tamper prev_hash at index 1
    tampered_entries = [e.model_copy() for e in entries]
    tampered_entries[1].prev_hash = "f" * 64
    res = verify_chain(tampered_entries)
    assert res.is_valid is False
    assert res.broken_index == 1

    # 2. Tamper event payload at index 2
    tampered_entries2 = [e.model_copy() for e in entries]
    tampered_entries2[2].event_payload = {"step": 2, "val": 999}
    res2 = verify_chain(tampered_entries2)
    assert res2.is_valid is False
    assert res2.broken_index == 2


@pytest.mark.asyncio
async def test_replay_determinism() -> None:
    """Replaying recorded audit log snapshot yields identical findings and risk score."""
    async with async_session_factory() as db:
        dossier_id = f"dos-replay-{uuid.uuid4().hex[:6]}"
        dossier = ApplicationDossier(
            dossier_id=dossier_id,
            institution_name="Deterministic Institute of Scrutiny",
            application_number=f"APP-{uuid.uuid4().hex[:6]}",
            program="Engineering & Technology",
            level="Under Graduate (UG)",
            institution_type="Private-Self Financing",
            location_type="Urban",
            intake_proposed=300,
            documents=[],
            findings=[],
            overall_status=VerificationStatus.PASS,
            risk_score=5.0,
            summary="All statutory checks passed.",
        )

        eval_findings = rule_engine.evaluate_dossier(dossier, dossier.documents, extracted_params={})
        dossier.findings = eval_findings

        has_fail = any(f.status == VerificationStatus.FAIL for f in eval_findings)
        has_review = any(f.status == VerificationStatus.MANUAL_REVIEW_REQUIRED for f in eval_findings)
        if has_fail:
            dossier.overall_status = VerificationStatus.FAIL
            dossier.risk_score = 75.0
        elif has_review:
            dossier.overall_status = VerificationStatus.MANUAL_REVIEW_REQUIRED
            dossier.risk_score = 40.0
        else:
            dossier.overall_status = VerificationStatus.PASS
            dossier.risk_score = 5.0

        audit_entry = await record_evaluation_audit(
            db=db,
            dossier=dossier,
            findings=eval_findings,
            evaluation_id=f"eval-test-{uuid.uuid4().hex[:8]}",
        )

        replay_result = await replay(evaluation_id=audit_entry.evaluation_id, db=db)
        assert replay_result.is_identical is True
        assert replay_result.diffs == []


@pytest.mark.asyncio
async def test_sse_event_order() -> None:
    """Async stage-by-stage event streaming order: ingest -> ocr -> forensics -> crypto -> extract -> rules -> graph -> completed."""
    async with async_session_factory() as db:
        dossier_id = f"dos-async-{uuid.uuid4().hex[:6]}"
        dm = DossierModel(
            dossier_id=dossier_id,
            institution_name="Async Test University",
            application_number=f"APP-ASYNC-{uuid.uuid4().hex[:6]}",
            program="Engineering & Technology",
            level="Under Graduate (UG)",
            institution_type="Private-Self Financing",
            location_type="Urban",
            intake_proposed=180,
        )
        db.add(dm)
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(f"/api/jobs/dossiers/{dossier_id}/evaluate")
        assert res.status_code == 200
        job_info = res.json()
        job_id = job_info["job_id"]

        for _ in range(30):
            job_check = await ac.get(f"/api/jobs/{job_id}")
            if job_check.json()["status"] in ("COMPLETED", "FAILED"):
                break
            await asyncio.sleep(0.1)

        history = broadcaster.get_history(job_id)
        assert len(history) >= 8

        stages_received = [e.stage for e in history]
        expected_stages = ["ingest", "ocr", "forensics", "crypto", "extract", "rules", "graph", "completed"]
        assert stages_received == expected_stages

        progress_values = [e.progress for e in history]
        assert progress_values == sorted(progress_values)
        assert progress_values[-1] == 100

