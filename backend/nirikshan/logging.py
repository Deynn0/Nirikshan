"""Structured JSON logging with request correlation IDs and latency tracking."""

from __future__ import annotations

import contextvars
import json
import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# Context variable for request tracing
correlation_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default="system"
)


class JSONFormatter(logging.Formatter):
    """Formats log records as structured, single-line JSON strings."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_ctx.get(),
        }

        # Include custom extra attributes if present
        if hasattr(record, "request_path"):
            log_data["path"] = record.request_path
        if hasattr(record, "request_method"):
            log_data["method"] = record.request_method
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def configure_structured_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure root and nirikshan loggers to emit JSON records."""
    logger = logging.getLogger("nirikshan")
    logger.setLevel(level)
    logger.handlers.clear()

    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = configure_structured_logging()


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Attaches correlation ID to every HTTP request and logs structured performance metrics."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        cid = request.headers.get("X-Correlation-ID") or f"req-{uuid.uuid4().hex[:10]}"
        token = correlation_id_ctx.set(cid)

        start_time = time.perf_counter()
        response: Response | None = None
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Correlation-ID"] = cid
            return response
        finally:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                f"{request.method} {request.url.path} {status_code} in {duration_ms}ms",
                extra={
                    "request_path": request.url.path,
                    "request_method": request.method,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )
            correlation_id_ctx.reset(token)
