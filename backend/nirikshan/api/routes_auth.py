"""API routes for authentication and token issuance."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from nirikshan.api.auth import (
    LoginRequest,
    TokenResponse,
    UserPrincipal,
    create_token,
    get_current_user,
)
from nirikshan.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(payload: LoginRequest) -> TokenResponse:
    """Issue a signed JWT access token for testing or offline deployment."""
    user_id = f"usr-{uuid.uuid4().hex[:8]}"
    token = create_token(
        user_id=user_id,
        username=payload.username,
        role=payload.role,
        institution_id=payload.institution_id,
        expiry_hours=settings.jwt_expiry_hours,
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=payload.role.value,
        username=payload.username,
        expires_in_hours=settings.jwt_expiry_hours,
    )


@router.get("/demo-accounts")
async def get_demo_accounts():
    """Return pre-configured synthetic profiles for regulatory testing."""
    return {
        "accounts": [
            {
                "id": "off-1",
                "username": "officer",
                "role": "officer",
                "display_name": "Dr. Arvind Sharma (Scrutiny Officer)",
                "role_label": "AICTE scrutiny officer",
            },
            {
                "id": "ver-1",
                "username": "verifier",
                "role": "verifier",
                "display_name": "S. K. Verma (Verification Cell)",
                "role_label": "Verification cell",
            },
            {
                "id": "adm-1",
                "username": "admin",
                "role": "admin",
                "display_name": "Chief Auditor (Admin)",
                "role_label": "Administrator / auditor",
            },
            {
                "id": "inst-1",
                "username": "inst1",
                "role": "institution",
                "institution": "Apex Institute of Technology & Management (A1)",
                "display_name": "Apex Institute Registrar (A1)",
            },
            {
                "id": "inst-2",
                "username": "inst2",
                "role": "institution",
                "institution": "Trinity Polytechnic Institute (A2)",
                "display_name": "Trinity Polytechnic Principal (A2)",
            },
            {
                "id": "inst-3",
                "username": "inst3",
                "role": "institution",
                "institution": "Pioneer College of Pharmacy (A3)",
                "display_name": "Pioneer Pharmacy Dean (A3)",
            },
            {
                "id": "inst-4",
                "username": "inst4",
                "role": "institution",
                "institution": "Saraswati School of Management (A4)",
                "display_name": "Saraswati Management Director (A4)",
            },
            {
                "id": "inst-5",
                "username": "inst5",
                "role": "institution",
                "institution": "Deccan College of Engineering & Research (A5)",
                "display_name": "Deccan College Registrar (A5)",
            },
            {
                "id": "inst-6",
                "username": "inst6",
                "role": "institution",
                "institution": "Sterling Global Institute (A6)",
                "display_name": "Sterling Global Director (A6)",
            },
            {
                "id": "inst-7",
                "username": "inst7",
                "role": "institution",
                "institution": "Vardhaman Institute of Technology (A7)",
                "display_name": "Vardhaman Tech Dean (A7)",
            },
            {
                "id": "inst-8",
                "username": "inst8",
                "role": "institution",
                "institution": "National Institute of Engineering & Technology (A8)",
                "display_name": "NIET Nanded Registrar (A8)",
            },
            {
                "id": "inst-9",
                "username": "inst9",
                "role": "institution",
                "institution": "Vidya Bharati Institute of Pharmaceutical Sciences (A9)",
                "display_name": "Vidya Bharati Principal (A9)",
            },
            {
                "id": "inst-10",
                "username": "inst10",
                "role": "institution",
                "institution": "Rajiv Gandhi College of Computer Applications (A10)",
                "display_name": "RGCCA Director (A10)",
            },
            {
                "id": "inst-11",
                "username": "inst11",
                "role": "institution",
                "institution": "K. J. Somaiya Polytechnic & Engineering Academy (A11)",
                "display_name": "K.J. Somaiya Principal (A11)",
            },
        ],
        "password": "demo-password",
        "notice": "Valid usernames: officer, verifier, admin, or inst1 to inst11 (Applications A1 to A11)",
    }


@router.get("/me", response_model=UserPrincipal)
async def get_current_user_profile(
    current_user: UserPrincipal = Depends(get_current_user),
) -> UserPrincipal:
    """Return currently authenticated principal and active scrutiny role."""
    return current_user
