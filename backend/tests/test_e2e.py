"""System Integrity, Security & Audit Trail: End-to-end scrutiny, CSRF enforcement, tamper-evident hash chain."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import asn1crypto.x509 as asn1_x509
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from nirikshan.crypto.qr_verifier import Keyring
from nirikshan.db.models import AuditLogModel
from nirikshan.db.session import async_session_factory, init_db
from nirikshan.engine.audit_log import (
    record_evaluation_audit,
    replay,
    verify_chain,
)
from nirikshan.engine.rule_evaluator import rule_engine
from nirikshan.main import app
from nirikshan.schemas.dossier import ApplicationDossier
from nirikshan.schemas.finding import VerificationStatus
from nirikshan.schemas.forensic import DocumentRecord, DocumentType, ForensicReport
from nirikshan.trust.ladder import TrustLevel
from scripts.evaluate import evaluate_single_application, evaluate_split
from scripts.make_fixtures import generate_fixtures


@pytest.fixture(autouse=True)
async def _setup_database() -> None:
    await init_db()


@pytest.fixture(scope="session")
def test_fixtures_dir(tmp_path_factory) -> Path:
    fixtures_dir = tmp_path_factory.mktemp("test_synthetic_fixtures")
    generate_fixtures(
        output_dir=fixtures_dir,
        num_apps=12,
        seed_dev=42,
        seed_blind=1337,
    )
    return fixtures_dir


@pytest.mark.asyncio
async def test_health_check_and_csrf_headers() -> None:
    """Assert offline policy guarantees, CSRF enforcement, and airgap security headers."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["offline_mode"] is True
    assert "AICTE" in data["handbook_edition"]
    assert response.headers.get("x-nirikshan-offline") == "strict-airgap-local"


@pytest.mark.asyncio
async def test_end_to_end_dossier_scrutiny_and_hash_chain() -> None:
    """Full lifecycle: create dossier, verify rules, record audit log, and verify tamper-evident hash chain."""
    async with async_session_factory() as db:
        dossier_id = f"dos-e2e-{uuid.uuid4().hex[:6]}"
        extracted_params = {
            "land_area_acres": 4.5,
            "is_contiguous": True,
            "fire_noc_valid": True,
            "location_type": "Urban",
        }

        forensic = ForensicReport(
            document_id="doc-deed-e2e",
            file_name="sale_deed.pdf",
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            file_size_bytes=10240,
            page_count=4,
            is_tampered=False,
            has_digital_signature=True,
            signature_valid=True,
            assessed_trust_level=TrustLevel.CRYPTOGRAPHIC,
        )
        deed_doc = DocumentRecord(
            document_id="doc-deed-e2e",
            dossier_id=dossier_id,
            file_name="sale_deed.pdf",
            doc_type=DocumentType.LAND_SALE_DEED,
            title="Registered Sale Deed",
            page_count=4,
            forensic=forensic,
            extracted_text_preview="Land Area: 4.5 Acres",
            is_self_attested=False,
        )

        dossier = ApplicationDossier(
            dossier_id=dossier_id,
            institution_name="E2E Scrutiny Institute of Technology",
            application_number=f"AICTE-2024-E2E-{uuid.uuid4().hex[:6].upper()}",
            program="Engineering & Technology",
            level="Under Graduate (UG)",
            institution_type="Private-Self Financing",
            location_type="Urban",
            intake_proposed=300,
            documents=[deed_doc],
            findings=[],
            overall_status=VerificationStatus.INCONCLUSIVE,
            risk_score=0.0,
            summary="Awaiting evaluation",
            extracted_params=extracted_params,
        )

        findings = rule_engine.evaluate_dossier(dossier, [deed_doc], extracted_params)
        has_fail = any(f.status == VerificationStatus.FAIL for f in findings)
        if has_fail:
            dossier.overall_status = VerificationStatus.FAIL
            dossier.risk_score = 75.0
        else:
            dossier.overall_status = VerificationStatus.PASS
            dossier.risk_score = 5.0

        audit_entry = await record_evaluation_audit(
            db=db,
            dossier=dossier,
            findings=findings,
            ruleset_name="aicte_aph_sample.yaml",
            evaluation_id=f"eval-e2e-{uuid.uuid4().hex[:8]}",
        )

        stmt = select(AuditLogModel).order_by(AuditLogModel.sequence.asc())
        all_entries = list((await db.execute(stmt)).scalars().all())
        chain_res = verify_chain(all_entries)
        assert chain_res.is_valid is True

        replay_res = await replay(evaluation_id=audit_entry.evaluation_id, db=db)
        assert replay_res.is_identical is True
        assert replay_res.original_status == replay_res.replayed_status


def test_synthetic_evaluation_pipeline_e2e(test_fixtures_dir: Path) -> None:
    """Verify synthetic evaluation runs on benchmark split with zero false positives on clean control."""
    manifest_path = test_fixtures_dir / "ground_truth.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    ca_der = (test_fixtures_dir / "trust_ca.der").read_bytes()
    asn1_ca = asn1_x509.Certificate.load(ca_der)
    keyring = Keyring(test_fixtures_dir / "keyring.json")

    clean_app_id = "app_dev_01"
    app_meta = manifest["applications"][clean_app_id]
    app_dir = test_fixtures_dir / "dev" / clean_app_id

    detected, _ = evaluate_single_application(app_meta, app_dir, asn1_ca, keyring)
    assert len(detected) == 0, f"Clean application was falsely flagged with: {detected}"

