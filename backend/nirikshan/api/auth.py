"""Role-based authentication and authorization (applicant vs officer)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from fastapi import Depends, Header, HTTPException, Request, status
from pydantic import BaseModel

from nirikshan.config import settings


class UserRole(StrEnum):
    APPLICANT = "applicant"
    OFFICER = "officer"


class UserPrincipal(BaseModel):
    """Authenticated user principal."""

    user_id: str
    username: str
    role: UserRole
    full_name: str = ""
    institution_id: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    expires_in_hours: int


class LoginRequest(BaseModel):
    username: str
    role: UserRole = UserRole.APPLICANT
    password: str = "offline-pass"
    institution_id: str | None = None


def create_token(
    user_id: str,
    username: str,
    role: UserRole,
    institution_id: str | None = None,
    expiry_hours: int | None = None,
) -> str:
    """Create a tamper-proof cryptographically signed access token (HMAC-SHA256)."""
    hrs = expiry_hours or settings.jwt_expiry_hours
    exp_dt = datetime.now(UTC) + timedelta(hours=hrs)
    payload = {
        "sub": user_id,
        "username": username,
        "role": role.value,
        "institution_id": institution_id,
        "exp": int(exp_dt.timestamp()),
        "jti": uuid.uuid4().hex,
    }
    header = {"alg": "HS256", "typ": "JWT"}

    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signing_input = f"{header_b64}.{payload_b64}"

    sig = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode().rstrip("=")

    return f"{signing_input}.{sig_b64}"


def verify_token(token: str) -> UserPrincipal:
    """Verify cryptographic signature and expiration of access token."""
    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}"

    expected_sig = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")

    if not hmac.compare_digest(sig_b64, expected_sig_b64):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signature.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Pad base64 payload if needed
    rem = len(payload_b64) % 4
    if rem > 0:
        payload_b64 += "=" * (4 - rem)

    try:
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode()).decode())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to decode token payload: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    exp = payload.get("exp", 0)
    if datetime.now(UTC).timestamp() > exp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role_str = payload.get("role", UserRole.APPLICANT.value)
    role_enum = UserRole(role_str) if role_str in UserRole.__members__.values() else UserRole.APPLICANT

    return UserPrincipal(
        user_id=payload.get("sub", "usr-anonymous"),
        username=payload.get("username", "anonymous"),
        role=role_enum,
        institution_id=payload.get("institution_id"),
    )


async def get_current_user(
    request: Request,
    authorization: str | None = Header(default=None),
    x_role: str | None = Header(default=None, alias="X-Nirikshan-Role"),
    x_username: str | None = Header(default=None, alias="X-Nirikshan-User"),
) -> UserPrincipal:
    """Extract authenticated user principal from Bearer token or role test headers."""
    # 1. Bearer Token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        return verify_token(token)

    # 2. Direct Header Support (Useful for offline airgap testing & local dev)
    if x_role:
        role_clean = x_role.lower().strip()
        role_enum = UserRole.OFFICER if role_clean == "officer" else UserRole.APPLICANT
        return UserPrincipal(
            user_id=f"usr-{role_enum.value}",
            username=x_username or f"local_{role_enum.value}",
            role=role_enum,
        )

    # 3. Default to applicant for backwards compatibility
    return UserPrincipal(
        user_id="usr-default-applicant",
        username="applicant_default",
        role=UserRole.APPLICANT,
    )


def require_role(allowed_roles: list[UserRole]):
    """Enforce that current user possesses one of the allowed roles."""

    async def _role_guard(current_user: UserPrincipal = Depends(get_current_user)) -> UserPrincipal:
        if current_user.role not in allowed_roles:
            allowed_names = [r.value for r in allowed_roles]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access Denied: Role '{current_user.role.value}' is not authorized. Required: {allowed_names}",
            )
        return current_user

    return _role_guard


require_officer = require_role([UserRole.OFFICER])
require_applicant = require_role([UserRole.APPLICANT])
require_any_authenticated = require_role([UserRole.APPLICANT, UserRole.OFFICER])
