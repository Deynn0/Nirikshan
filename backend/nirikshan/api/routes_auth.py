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


@router.get("/me", response_model=UserPrincipal)
async def get_current_user_profile(
    current_user: UserPrincipal = Depends(get_current_user),
) -> UserPrincipal:
    """Return currently authenticated principal and active scrutiny role."""
    return current_user
