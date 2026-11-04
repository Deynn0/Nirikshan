"""Pytest fixtures, test client, in-memory DB, auth & seeded data."""

from __future__ import annotations

import logging
import os
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.testclient import TestClient

# Isolate every test session before nirikshan is imported
_TMP = Path(tempfile.mkdtemp(prefix="nirikshan-test-"))
os.environ["NIRIKSHAN_DATA_DIR"] = str(_TMP)
_trust_src = Path(__file__).resolve().parents[1] / "trust"
if _trust_src.exists():
    shutil.copytree(_trust_src, _TMP / "trust", dirs_exist_ok=True, ignore=shutil.ignore_patterns("demo"))
os.environ["NIRIKSHAN_TRUST_DIR"] = str(_TMP / "trust")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

for _n in ("pyhanko", "pyhanko_certvalidator", "pdfminer", "RapidOCR"):
    logging.getLogger(_n).setLevel(logging.CRITICAL)

from nirikshan.api.auth import UserRole, create_token
from nirikshan.api.rate_limiter import rate_limiter
from nirikshan.db.session import async_session_factory, init_db
from nirikshan.main import app


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """Reset the sliding window rate limiter before every test."""
    rate_limiter.reset()
    yield


@pytest.fixture(autouse=True)
async def _setup_in_memory_db():
    """Ensure database schema is created prior to test requests."""
    await init_db()
    yield


@pytest.fixture
def test_client() -> TestClient:
    """Synchronous Starlette/FastAPI TestClient fixture."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Asynchronous HTTP test client bound to Nirikshan FastAPI app."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def officer_token() -> str:
    """Valid JWT token for an officer with scrutiny privileges."""
    return create_token(
        user_id="officer-scrutiny-01",
        username="officer.verma",
        role=UserRole.OFFICER,
    )


@pytest.fixture
def applicant_token() -> str:
    """Valid JWT token for an applicant institution."""
    return create_token(
        user_id="applicant-inst-01",
        username="principal.apex",
        role=UserRole.APPLICANT,
        institution_id="INST-APEX-001",
    )


@pytest.fixture
def officer_headers(officer_token: str) -> dict[str, str]:
    """Auth headers for scrutiny desk officer."""
    return {"Authorization": f"Bearer {officer_token}"}


@pytest.fixture
def applicant_headers(applicant_token: str) -> dict[str, str]:
    """Auth headers for applicant institution."""
    return {"Authorization": f"Bearer {applicant_token}"}


@pytest.fixture
def seeded_dossier_data() -> dict:
    """Sample application dossier data payload conforming to AICTE APH."""
    app_num = f"AICTE-2024-APEX-{uuid.uuid4().hex[:6].upper()}"
    return {
        "institution_name": "Apex Institute of Engineering & Technology",
        "application_number": app_num,
        "program": "Engineering & Technology",
        "level": "Under Graduate (UG)",
        "institution_type": "Private-Self Financing",
        "location_type": "Urban",
        "intake_proposed": 300,
    }
