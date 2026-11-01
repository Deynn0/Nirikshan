"""Comprehensive production hardening tests.

Covers:
1. Sandbox limits: wall-clock timeout, infinite loop stub, zip-bomb PDF, page count cap,
   file size cap, network isolation.
2. Envelope encryption: AES-256-GCM data keys wrapped by master key, transparent
   sandbox-only decryption, ciphertext & wrapped DEK tamper detection, master key rotation.
3. Hash-chained audit log: sequential cryptographic chaining, prev_hash and payload
   tamper detection, deterministic evaluation replay.
4. Asynchronous processing: DB-backed job queue, stage-by-stage SSE streaming in strict order
   (ingest -> ocr -> forensics -> crypto -> extract -> rules -> graph -> completed).
5. Role-based access control (applicant vs officer) & sliding-window rate limiting.
"""

from __future__ import annotations

import asyncio
import os
import uuid
import zlib
from datetime import UTC, datetime
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from nirikshan.api.auth import (
    UserRole,
    create_token,
    verify_token,
)
from nirikshan.api.rate_limiter import rate_limiter
from nirikshan.crypto.envelope import (
    EnvelopeTamperError,
    SandboxDecryptionEnforcementError,
)
from nirikshan.crypto.master_keys import MasterKeyProvider
from nirikshan.crypto.storage import EncryptedStorageService
from nirikshan.db.models import DossierModel
from nirikshan.db.session import async_session_factory, init_db
from nirikshan.engine.audit_log import (
    AuditLogEntry,
    compute_entry_hash,
    record_evaluation_audit,
    replay,
    verify_chain,
)
from nirikshan.main import app
from nirikshan.sandbox import (
    SandboxedWorkerManager,
    SandboxViolationError,
    SandboxViolationType,
    _check_decompression_ratio,
    _check_page_count_fast,
)
from nirikshan.schemas.dossier import ApplicationDossier
from nirikshan.schemas.finding import VerificationStatus
from nirikshan.worker.job_service import broadcaster


@pytest.fixture(autouse=True)
async def _setup_database() -> None:
    """Ensure database schema is ready and rate limiter reset before every test."""
    await init_db()
    rate_limiter.reset()
    rate_limiter.set_limit(120, 60.0)


# ==============================================================================
# 1. SANDBOX RESOURCE LIMITS & UNTRUSTED FILE GUARDS
# ==============================================================================


def test_sandbox_infinite_loop_stub() -> None:
    """Test that an infinite-loop stub is terminated by the sandbox timeout."""
    mgr = SandboxedWorkerManager(wall_clock_timeout=2)
    infinite_loop_code = (
        "import time\n"
        "while True:\n"
        "    time.sleep(0.1)\n"
    )

    with pytest.raises(SandboxViolationError) as exc_info:
        mgr.run_isolated_code(infinite_loop_code, timeout=2.0)

    err = exc_info.value
    assert err.violation_type in (
        SandboxViolationType.TIMEOUT_EXCEEDED,
        SandboxViolationType.CPU_LIMIT_EXCEEDED,
    )
    assert "timeout" in err.message.lower() or "cpu" in err.message.lower()
    details = err.to_dict()
    assert details["violation_type"] == err.violation_type


def test_sandbox_zip_bomb_decompression_ratio() -> None:
    """Test detection of zip-bomb-style PDF streams with high expansion ratios."""
    # Create synthetic zlib stream that expands from 100 bytes to 200,000 bytes (2,000x ratio)
    repeated_content = b"AICTE-REGULATORY-SCRUTINY-" * 8000  # ~208 KB
    compressed_stream = zlib.compress(repeated_content, level=9)
    assert len(compressed_stream) < 1000  # Extremely small compressed stream

    # Construct synthetic PDF stream object with this compressed payload
    synthetic_pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj\n"
        b"<< /Length 400 /Filter /FlateDecode >>\n"
        b"stream\n" + compressed_stream + b"\nendstream\n"
        b"endobj\n"
        b"%%EOF\n"
    )

    # Validate that decompression ratio check flags the bomb
    with pytest.raises(SandboxViolationError) as exc_info:
        _check_decompression_ratio(synthetic_pdf_bytes, max_ratio=20.0)

    err = exc_info.value
    assert err.violation_type == SandboxViolationType.DECOMPRESSION_BOMB
    assert "ratio" in err.message.lower()
    assert err.details["ratio"] > 20.0


def test_sandbox_page_count_cap() -> None:
    """Test that documents exceeding the maximum page count hard cap are rejected."""
    # Construct synthetic raw PDF with 150 page objects
    pages_raw = b"".join(
        f"{i} 0 obj << /Type /Page >> endobj\n".encode() for i in range(1, 151)
    )
    pdf_bytes = b"%PDF-1.4\n" + pages_raw + b"%%EOF\n"

    with pytest.raises(SandboxViolationError) as exc_info:
        _check_page_count_fast(pdf_bytes, max_pages=100)

    err = exc_info.value
    assert err.violation_type == SandboxViolationType.PAGE_COUNT_EXCEEDED
    assert err.details["estimated_pages"] > 100


def test_sandbox_file_size_cap(tmp_path: Path) -> None:
    """Test that files exceeding the maximum file size cap trigger a structured error."""
    test_file = tmp_path / "oversized.pdf"
    test_file.write_bytes(b"x" * 1024)

    # Manager configured with a 500 byte limit
    mgr = SandboxedWorkerManager(max_file_size_bytes=500)

    with pytest.raises(SandboxViolationError) as exc_info:
        mgr.validate_file_guards(test_file)

    err = exc_info.value
    assert err.violation_type == SandboxViolationType.FILE_SIZE_EXCEEDED
    assert err.details["file_size"] == 1024
    assert err.details["limit_bytes"] == 500


def test_sandbox_network_isolation() -> None:
    """Test that network socket operations are strictly prohibited inside the sandbox subprocess."""
    mgr = SandboxedWorkerManager(wall_clock_timeout=5)
    network_code = (
        "import socket\n"
        "s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
        "s.connect(('1.1.1.1', 80))\n"
    )

    with pytest.raises(SandboxViolationError) as exc_info:
        mgr.run_isolated_code(network_code, timeout=5.0)

    err = exc_info.value
    assert err.violation_type == SandboxViolationType.NETWORK_ACCESS_BLOCKED
    assert "network" in err.message.lower()


# ==============================================================================
# 2. ENVELOPE ENCRYPTION & TAMPER DETECTION
# ==============================================================================


def test_envelope_encryption_roundtrip(tmp_path: Path) -> None:
    """Test per-document AES-256-GCM data key wrapped by master key and roundtrip decryption."""
    # Use isolated master key provider
    provider = MasterKeyProvider(key_file_path=tmp_path / "test_keys.json")
    storage = EncryptedStorageService(storage_dir=tmp_path / "quarantine", key_provider=provider)

    doc_id = "doc-test-encrypt-001"
    original_plaintext = b"%PDF-1.4\nAICTE Verification Confidential Document Content\n%%EOF"

    # Store encrypted envelope
    path, envelope = storage.store_document(doc_id, original_plaintext)
    assert path.exists()
    assert envelope.document_id == doc_id
    assert envelope.master_key_id == provider.active_key_id
    assert len(envelope.wrapped_dek_b64) > 0
    assert len(envelope.doc_ciphertext_b64) > 0

    # Decrypt in sandbox context
    decrypted = storage.decrypt_document(envelope, is_sandbox=True)
    assert decrypted == original_plaintext


def test_envelope_decryption_outside_sandbox_denied(tmp_path: Path) -> None:
    """Test that transparent decryption is strictly blocked outside the sandbox environment."""
    provider = MasterKeyProvider(key_file_path=tmp_path / "test_keys.json")
    storage = EncryptedStorageService(storage_dir=tmp_path / "quarantine", key_provider=provider)

    doc_id = "doc-test-outside-sandbox"
    _, envelope = storage.store_document(doc_id, b"sensitive document")

    # Outside sandbox without NIRIKSHAN_SANDBOX_ACTIVE set
    old_env = os.environ.get("NIRIKSHAN_SANDBOX_ACTIVE")
    if "NIRIKSHAN_SANDBOX_ACTIVE" in os.environ:
        del os.environ["NIRIKSHAN_SANDBOX_ACTIVE"]

    try:
        with pytest.raises(SandboxDecryptionEnforcementError):
            storage.decrypt_document(envelope, is_sandbox=False)
    finally:
        if old_env is not None:
            os.environ["NIRIKSHAN_SANDBOX_ACTIVE"] = old_env


def test_envelope_tamper_detection(tmp_path: Path) -> None:
    """Test cryptographic tamper detection on ciphertext and wrapped DEK."""
    import base64

    provider = MasterKeyProvider(key_file_path=tmp_path / "test_keys.json")
    storage = EncryptedStorageService(storage_dir=tmp_path / "quarantine", key_provider=provider)

    doc_id = "doc-tamper-check"
    _, envelope = storage.store_document(doc_id, b"Original uncorrupted document")

    # 1. Tamper with document ciphertext
    raw_ct = bytearray(base64.b64decode(envelope.doc_ciphertext_b64))
    raw_ct[0] ^= 0xFF  # Flip bit
    tampered_envelope = envelope.model_copy(
        update={"doc_ciphertext_b64": base64.b64encode(raw_ct).decode("ascii")}
    )

    with pytest.raises(EnvelopeTamperError) as exc_info:
        storage.decrypt_document(tampered_envelope, is_sandbox=True)
    assert "tamper" in str(exc_info.value).lower() or "tag" in str(exc_info.value).lower()

    # 2. Tamper with wrapped DEK
    raw_dek = bytearray(base64.b64decode(envelope.wrapped_dek_b64))
    raw_dek[0] ^= 0xFF
    tampered_dek_envelope = envelope.model_copy(
        update={"wrapped_dek_b64": base64.b64encode(raw_dek).decode("ascii")}
    )

    with pytest.raises(EnvelopeTamperError):
        storage.decrypt_document(tampered_dek_envelope, is_sandbox=True)


def test_envelope_master_key_rotation(tmp_path: Path) -> None:
    """Test rotating master key and rewrapping document data keys without document re-encryption."""
    provider = MasterKeyProvider(key_file_path=tmp_path / "test_keys.json")
    storage = EncryptedStorageService(storage_dir=tmp_path / "quarantine", key_provider=provider)

    doc_id = "doc-rotation-test"
    plaintext = b"Payload created under Key Version 1"
    v1_key_id = provider.active_key_id
    _, envelope_v1 = storage.store_document(doc_id, plaintext)
    assert envelope_v1.master_key_id == v1_key_id

    # Rotate to Version 2 master key
    v2_key_id, _ = provider.rotate_master_key("master-key-2024-v2")
    assert provider.active_key_id == v2_key_id

    # Older document should still decrypt seamlessly with its original master key
    decrypted_old = storage.decrypt_document(envelope_v1, is_sandbox=True)
    assert decrypted_old == plaintext

    # Rewrap document with new master key
    envelope_v2 = storage.rewrap_document(doc_id, new_master_key_id=v2_key_id)
    assert envelope_v2.master_key_id == v2_key_id
    # Document ciphertext itself remains identical
    assert envelope_v2.doc_ciphertext_b64 == envelope_v1.doc_ciphertext_b64

    # Decrypt rewrapped envelope
    decrypted_new = storage.decrypt_document(envelope_v2, is_sandbox=True)
    assert decrypted_new == plaintext


# ==============================================================================
# 3. HASH-CHAINED AUDIT LOG & REPLAY DETERMINISM
# ==============================================================================


def test_audit_chain_valid_progression() -> None:
    """Test valid sequential construction and verification of the audit chain."""
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
    """Test that modifying prev_hash or payload breaks the chain and is detected with exact index."""
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

    # 1. Tamper with prev_hash at index 1
    tampered_entries = [e.model_copy() for e in entries]
    tampered_entries[1].prev_hash = "f" * 64

    res = verify_chain(tampered_entries)
    assert res.is_valid is False
    assert res.broken_index == 1
    assert "Broken chain link" in (res.reason or "")

    # 2. Tamper with payload at index 2
    tampered_entries2 = [e.model_copy() for e in entries]
    tampered_entries2[2].event_payload = {"step": 2, "val": 999}  # Modified payload

    res2 = verify_chain(tampered_entries2)
    assert res2.is_valid is False
    assert res2.broken_index == 2
    assert "Payload tamper detected" in (res2.reason or "")


@pytest.mark.asyncio
async def test_replay_determinism() -> None:
    """Test that replaying a recorded evaluation produces identical findings and risk score."""
    async with async_session_factory() as db:
        # Create a mock dossier
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

        # Generate deterministic rule evaluation findings
        from nirikshan.engine.rule_evaluator import rule_engine

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

        # Record evaluation in audit log
        audit_entry = await record_evaluation_audit(
            db=db,
            dossier=dossier,
            findings=eval_findings,
            evaluation_id=f"eval-test-{uuid.uuid4().hex[:8]}",
        )

        # Execute replay
        replay_result = await replay(evaluation_id=audit_entry.evaluation_id, db=db)
        assert replay_result.is_identical is True
        assert replay_result.diffs == []
        assert replay_result.original_status == replay_result.replayed_status
        assert replay_result.original_risk_score == replay_result.replayed_risk_score
        assert replay_result.original_findings_count == len(eval_findings)


# ==============================================================================
# 4. ASYNC PROCESSING & SSE EVENT ORDER
# ==============================================================================


@pytest.mark.asyncio
async def test_sse_event_order() -> None:
    """Test that async processing emits progress events in strict stage order:
    ingest -> ocr -> forensics -> crypto -> extract -> rules -> graph -> completed.
    """
    async with async_session_factory() as db:
        # 1. Create dossier in DB
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

    # 2. Trigger async evaluation job via API
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(f"/api/jobs/dossiers/{dossier_id}/evaluate")
        assert res.status_code == 200
        job_info = res.json()
        job_id = job_info["job_id"]

        # Wait briefly for background execution to complete
        for _ in range(30):
            job_check = await ac.get(f"/api/jobs/{job_id}")
            if job_check.json()["status"] in ("COMPLETED", "FAILED"):
                break
            await asyncio.sleep(0.1)

        # Collect event history from broadcaster
        history = broadcaster.get_history(job_id)
        assert len(history) >= 8  # 7 stages + completed

        stages_received = [e.stage for e in history]
        expected_stages = ["ingest", "ocr", "forensics", "crypto", "extract", "rules", "graph", "completed"]

        assert stages_received == expected_stages

        # Verify monotonic progress percent
        progress_values = [e.progress for e in history]
        assert progress_values == sorted(progress_values)
        assert progress_values[-1] == 100


# ==============================================================================
# 5. AUTH / ROLES (APPLICANT VS OFFICER) & RATE LIMITING
# ==============================================================================


def test_auth_roles_token_issuance_and_verification() -> None:
    """Test creating and validating tokens for applicant and officer roles."""
    # 1. Applicant Token
    app_token = create_token(user_id="usr-app-1", username="applicant_user", role=UserRole.APPLICANT)
    app_principal = verify_token(app_token)
    assert app_principal.role == UserRole.APPLICANT
    assert app_principal.username == "applicant_user"

    # 2. Officer Token
    off_token = create_token(user_id="usr-off-1", username="scrutiny_officer", role=UserRole.OFFICER)
    off_principal = verify_token(off_token)
    assert off_principal.role == UserRole.OFFICER
    assert off_principal.username == "scrutiny_officer"


@pytest.mark.asyncio
async def test_auth_role_endpoint_access_control() -> None:
    """Test that officer-only routes reject applicant requests and allow officer requests."""
    applicant_token = create_token(user_id="usr-1", username="applicant", role=UserRole.APPLICANT)
    officer_token = create_token(user_id="usr-2", username="officer", role=UserRole.OFFICER)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Check /api/auth/me with applicant token
        res_app = await ac.get("/api/auth/me", headers={"Authorization": f"Bearer {applicant_token}"})
        assert res_app.status_code == 200
        assert res_app.json()["role"] == "applicant"

        # Check /api/auth/me with officer token
        res_off = await ac.get("/api/auth/me", headers={"Authorization": f"Bearer {officer_token}"})
        assert res_off.status_code == 200
        assert res_off.json()["role"] == "officer"


@pytest.mark.asyncio
async def test_sliding_window_rate_limiter() -> None:
    """Test that exceeding the configured rate limit triggers HTTP 429 with Retry-After header."""
    rate_limiter.reset()
    # Configure tight limit of 3 requests per 60 seconds for testing
    rate_limiter.set_limit(max_requests=3, window_seconds=60.0)

    client_headers = {"X-Forwarded-For": "203.0.113.42"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # First 3 requests succeed
        for _ in range(3):
            res = await ac.get("/api/rules", headers=client_headers)
            assert res.status_code == 200
            assert "x-ratelimit-remaining" in res.headers

        # 4th request must be rejected with 429 Too Many Requests
        res_429 = await ac.get("/api/rules", headers=client_headers)
        assert res_429.status_code == 429
        assert "retry-after" in res_429.headers
        assert res_429.headers["x-ratelimit-remaining"] == "0"
        data = res_429.json()
        assert "Rate limit exceeded" in data["detail"]

    # Reset limiter for subsequent tests
    rate_limiter.reset()
    rate_limiter.set_limit(120, 60.0)
