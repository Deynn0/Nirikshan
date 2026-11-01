"""Integration tests for FastAPI scrutiny endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from nirikshan.db.session import init_db
from nirikshan.main import app


@pytest.fixture(autouse=True)
async def _setup_database() -> None:
    """Ensure database schema is created prior to test requests."""
    await init_db()


@pytest.mark.asyncio
async def test_health_check_endpoint() -> None:
    """Test health check asserting offline policy guarantees."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["offline_mode"] is True
    assert "AICTE" in data["handbook_edition"]
    # Check offline security header
    assert response.headers.get("x-nirikshan-offline") == "strict-airgap-local"


@pytest.mark.asyncio
async def test_rules_endpoint() -> None:
    """Test retrieval of AICTE Approval Process Handbook rules."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/rules")
    assert response.status_code == 200
    rules = response.json()
    assert len(rules) >= 8
    rule_ids = [r["id"] for r in rules]
    assert "AICTE-2024-LAND-001" in rule_ids
    assert "AICTE-2024-SAFE-001" in rule_ids


@pytest.mark.asyncio
async def test_dossier_lifecycle_and_verification() -> None:
    """Test creating a dossier, triggering verification, and generating report."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create dossier
        import uuid

        app_num = f"AICTE-2024-APEX-{uuid.uuid4().hex[:6]}"
        payload = {
            "institution_name": "Apex Engineering Institute",
            "application_number": app_num,
            "program": "Engineering & Technology",
            "level": "Under Graduate (UG)",
            "institution_type": "Private-Self Financing",
            "location_type": "Urban",
            "intake_proposed": 300,
        }
        res_create = await ac.post("/api/dossiers", json=payload)
        assert res_create.status_code == 200
        dossier = res_create.json()
        dossier_id = dossier["dossier_id"]

        # 2. Trigger verification
        res_verify = await ac.post(f"/api/dossiers/{dossier_id}/verify")
        assert res_verify.status_code == 200
        verified_data = res_verify.json()
        assert len(verified_data["findings"]) > 0

        # 3. Generate Scrutiny Report
        res_report = await ac.get(f"/api/dossiers/{dossier_id}/report")
        assert res_report.status_code == 200
        report = res_report.json()
        assert "trust_ladder_distribution" in report
        assert "regulatory_standard" in report
        assert len(report["findings"]) > 0
