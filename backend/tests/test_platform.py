"""System Integrity, Security & Audit Trail: Multi-tenant isolation, role-based authorization, rate limits."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from nirikshan.api.auth import UserRole, create_token, verify_token
from nirikshan.api.rate_limiter import rate_limiter
from nirikshan.db.session import init_db
from nirikshan.main import app


@pytest.fixture(autouse=True)
async def _setup_database() -> None:
    await init_db()
    rate_limiter.reset()
    rate_limiter.set_limit(120, 60.0)


# ---------------------------------------------------------------------------
# Role-Based Authorization
# ---------------------------------------------------------------------------

def test_auth_roles_token_issuance_and_verification() -> None:
    app_token = create_token(user_id="usr-app-1", username="applicant_user", role=UserRole.APPLICANT)
    app_principal = verify_token(app_token)
    assert app_principal.role == UserRole.APPLICANT
    assert app_principal.username == "applicant_user"

    off_token = create_token(user_id="usr-off-1", username="scrutiny_officer", role=UserRole.OFFICER)
    off_principal = verify_token(off_token)
    assert off_principal.role == UserRole.OFFICER
    assert off_principal.username == "scrutiny_officer"


@pytest.mark.asyncio
async def test_auth_role_endpoint_access_control() -> None:
    applicant_token = create_token(user_id="usr-1", username="applicant", role=UserRole.APPLICANT)
    officer_token = create_token(user_id="usr-2", username="officer", role=UserRole.OFFICER)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_app = await ac.get("/api/auth/me", headers={"Authorization": f"Bearer {applicant_token}"})
        assert res_app.status_code == 200
        assert res_app.json()["role"] == "applicant"

        res_off = await ac.get("/api/auth/me", headers={"Authorization": f"Bearer {officer_token}"})
        assert res_off.status_code == 200
        assert res_off.json()["role"] == "officer"


# ---------------------------------------------------------------------------
# Sliding-Window Rate Limiter
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sliding_window_rate_limiter() -> None:
    rate_limiter.reset()
    rate_limiter.set_limit(max_requests=3, window_seconds=60.0)

    client_headers = {"X-Forwarded-For": "203.0.113.42"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        for _ in range(3):
            res = await ac.get("/api/rules", headers=client_headers)
            assert res.status_code == 200
            assert "x-ratelimit-remaining" in res.headers

        res_429 = await ac.get("/api/rules", headers=client_headers)
        assert res_429.status_code == 429
        assert "retry-after" in res_429.headers
        assert res_429.headers["x-ratelimit-remaining"] == "0"
        data = res_429.json()
        assert "Rate limit exceeded" in data["detail"]

    rate_limiter.reset()
    rate_limiter.set_limit(120, 60.0)


# ---------------------------------------------------------------------------
# Multi-Tenant Isolation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_multi_tenant_dossier_isolation() -> None:
    """Institutions are partitioned and can only manage their own application dossiers."""
    tenant_a_token = create_token("usr-tenant-a", "principal.a", UserRole.APPLICANT, institution_id="INST-AAA")
    tenant_b_token = create_token("usr-tenant-b", "principal.b", UserRole.APPLICANT, institution_id="INST-BBB")

    headers_a = {"Authorization": f"Bearer {tenant_a_token}"}
    headers_b = {"Authorization": f"Bearer {tenant_b_token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create dossier for Tenant A
        res_create = await ac.post(
            "/api/dossiers",
            json={
                "institution_name": "Institution A Engineering College",
                "application_number": f"AICTE-2024-TENA-{uuid.uuid4().hex[:6].upper()}",
                "program": "Engineering & Technology",
                "level": "Under Graduate (UG)",
                "institution_type": "Private-Self Financing",
                "location_type": "Urban",
                "intake_proposed": 180,
            },
            headers=headers_a,
        )
        assert res_create.status_code == 200
        dossier_a_id = res_create.json()["dossier_id"]

        # Tenant A can fetch its dossier
        res_fetch_a = await ac.get(f"/api/dossiers/{dossier_a_id}", headers=headers_a)
        assert res_fetch_a.status_code == 200
        assert res_fetch_a.json()["dossier_id"] == dossier_a_id

