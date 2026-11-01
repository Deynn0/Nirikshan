"""Nirikshan Scrutiny Application FastAPI server."""

import socket
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from nirikshan.api.rate_limiter import RateLimitMiddleware
from nirikshan.api.routes_advisory import router as advisory_router
from nirikshan.api.routes_audit import router as audit_router
from nirikshan.api.routes_auth import router as auth_router
from nirikshan.api.routes_documents import router as documents_router
from nirikshan.api.routes_dossiers import router as dossiers_router
from nirikshan.api.routes_fraud import router as fraud_router
from nirikshan.api.routes_jobs import router as jobs_router
from nirikshan.api.routes_reports import router as reports_router
from nirikshan.api.routes_rules import router as rules_router
from nirikshan.api.routes_scan import router as scan_router
from nirikshan.config import settings
from nirikshan.db.session import init_db
from nirikshan.logging import StructuredLoggingMiddleware


def _install_airgap_guard() -> None:
    """Enforce zero outbound external network connections at runtime under Nirikshan constitution."""
    if settings.allow_external_network:
        return
    orig_connect = socket.socket.connect

    def _guarded_connect(self: socket.socket, address: Any) -> Any:
        host = address[0] if isinstance(address, tuple) and address else address
        host_str = str(host).lower()
        if host_str not in ("127.0.0.1", "localhost", "::1", "0.0.0.0") and not host_str.startswith("127."):
            raise PermissionError(
                f"Airgap Violation: Outbound network connection to '{host}' "
                "is strictly blocked at runtime under Nirikshan offline scrutiny constitution."
            )
        return orig_connect(self, address)

    socket.socket.connect = _guarded_connect  # type: ignore[assignment]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup and shutdown lifecycle handler."""
    # Enforce air-gapped network isolation
    _install_airgap_guard()
    # Initialize DB tables
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Offline-first explainable document verification system for AICTE regulatory scrutiny.",
    lifespan=lifespan,
)

# Structured JSON Logging Middleware
app.add_middleware(StructuredLoggingMiddleware)

# Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware)

# CORS configuration for Frontend Scrutiny Console
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def enforce_offline_headers(request: Any, call_next: Any) -> Any:
    """Ensure every response carries offline guarantees and security headers."""
    response = await call_next(request)
    response.headers["X-Nirikshan-Offline"] = "strict-airgap-local"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.get("/api/health")
async def health_check() -> JSONResponse:
    """System health check and offline policy verification."""
    return JSONResponse(
        content={
            "status": "healthy",
            "app": settings.app_name,
            "version": settings.app_version,
            "offline_mode": not settings.allow_external_network,
            "handbook_edition": settings.active_handbook_edition,
            "storage_ready": settings.quarantine_dir.exists(),
        }
    )


app.include_router(auth_router)
app.include_router(dossiers_router)
app.include_router(documents_router)
app.include_router(jobs_router)
app.include_router(audit_router)
app.include_router(rules_router)
app.include_router(reports_router)
app.include_router(scan_router)
app.include_router(advisory_router)
app.include_router(fraud_router)
