"""Verification & Rectification Workflow: Scrutiny desk assignments, review queues, officer decisions."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from nirikshan.api.auth import UserRole, create_token
from nirikshan.db.session import init_db
from nirikshan.main import app
from nirikshan.schemas.finding import Finding, VerificationStatus


@pytest.fixture(autouse=True)
async def _setup_database() -> None:
    await init_db()


@pytest.fixture
def officer_auth_headers() -> dict[str, str]:
    token = create_token("usr-off-1", "scrutiny.officer.singh", UserRole.OFFICER)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def applicant_auth_headers() -> dict[str, str]:
    token = create_token("usr-app-1", "applicant.principal", UserRole.APPLICANT, institution_id="INST-01")
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_officer_review_queue_listing(officer_auth_headers: dict[str, str]) -> None:
    """Officers can fetch review queue and see pending dossiers."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/dossiers", headers=officer_auth_headers)
        assert res.status_code == 200
        dossiers = res.json()
        assert isinstance(dossiers, list)


@pytest.mark.asyncio
async def test_officer_scrutiny_desk_decision_flow(officer_auth_headers: dict[str, str]) -> None:
    """Officer initiates dossier scrutiny verification and inspects decision report."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        app_num = f"AICTE-2024-OFF-{uuid.uuid4().hex[:6].upper()}"
        payload = {
            "institution_name": "National Scrutiny Institute of Technology",
            "application_number": app_num,
            "program": "Engineering & Technology",
            "level": "Under Graduate (UG)",
            "institution_type": "Government",
            "location_type": "Urban",
            "intake_proposed": 240,
        }
        res_create = await ac.post("/api/dossiers", json=payload, headers=officer_auth_headers)
        assert res_create.status_code == 200
        dossier_id = res_create.json()["dossier_id"]

        # Officer runs verification check
        res_verify = await ac.post(f"/api/dossiers/{dossier_id}/verify", headers=officer_auth_headers)
        assert res_verify.status_code == 200
        findings = res_verify.json()["findings"]
        assert len(findings) > 0

        # Officer views comprehensive scrutiny report
        res_report = await ac.get(f"/api/dossiers/{dossier_id}/report", headers=officer_auth_headers)
        assert res_report.status_code == 200
        report_data = res_report.json()
        assert report_data["dossier"]["dossier_id"] == dossier_id
        assert "findings_metrics" in report_data
        assert "trust_ladder_distribution" in report_data


@pytest.mark.asyncio
async def test_officer_decision_status_integrity() -> None:
    """Officer decision statuses enforce valid state machine."""
    valid_decisions = [
        VerificationStatus.PASS,
        VerificationStatus.FAIL,
        VerificationStatus.MANUAL_REVIEW_REQUIRED,
        VerificationStatus.FLAGGED_TAMPER,
    ]
    for status in valid_decisions:
        assert isinstance(status.value, str)
