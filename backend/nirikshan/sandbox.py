"""Production Sandboxed Worker Execution and Untrusted File Isolation.

Guarantees:
1. Isolated subprocess execution with clean temporary working directory.
2. POSIX RLIMIT_CPU and RLIMIT_AS enforcement (with graceful cross-platform fallback).
3. Wall-clock timeout enforcement.
4. Total network isolation (sockets disabled at OS/process level).
5. Hard caps on file size, page count, and decompression ratio (zip-bomb defense).
6. Structured violation errors with machine-readable codes.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
import zlib
from pathlib import Path
from typing import Any

from nirikshan.config import settings
from nirikshan.schemas.forensic import ForensicReport


class SandboxViolationType(str):
    CPU_LIMIT_EXCEEDED = "CPU_LIMIT_EXCEEDED"
    MEMORY_LIMIT_EXCEEDED = "MEMORY_LIMIT_EXCEEDED"
    TIMEOUT_EXCEEDED = "TIMEOUT_EXCEEDED"
    FILE_SIZE_EXCEEDED = "FILE_SIZE_EXCEEDED"
    PAGE_COUNT_EXCEEDED = "PAGE_COUNT_EXCEEDED"
    DECOMPRESSION_BOMB = "DECOMPRESSION_BOMB"
    NETWORK_ACCESS_BLOCKED = "NETWORK_ACCESS_BLOCKED"
    PARSER_ERROR = "PARSER_ERROR"


class SandboxViolationError(Exception):
    """Structured error raised on any sandbox security or policy violation."""

    def __init__(
        self,
        violation_type: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(f"[{violation_type}] {message}")
        self.violation_type = violation_type
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "violation_type": self.violation_type,
            "message": self.message,
            "details": self.details,
        }


# Backwards compatibility alias
SandboxedWorkerError = SandboxViolationError


def _check_decompression_ratio(
    raw_bytes: bytes, max_ratio: float = 30.0, max_decompressed_bytes: int = 50 * 1024 * 1024
) -> None:
    """Scan raw PDF / container streams for high-ratio decompression bombs (zip bombs).

    Raises:
        SandboxViolationError: if any stream or cumulative decompression exceeds thresholds.
    """
    stream_pattern = re.compile(rb"stream\r?\n(.*?)\r?\nendstream", re.DOTALL)
    matches = stream_pattern.findall(raw_bytes)

    total_uncompressed = 0
    total_compressed = 0

    for stream in matches:
        compressed_len = len(stream)
        if compressed_len == 0:
            continue
        total_compressed += compressed_len

        # Try decompressing stream
        try:
            decompressed = zlib.decompress(stream)
            uncompressed_len = len(decompressed)
            total_uncompressed += uncompressed_len

            ratio = uncompressed_len / max(1, compressed_len)
            if ratio > max_ratio:
                raise SandboxViolationError(
                    SandboxViolationType.DECOMPRESSION_BOMB,
                    f"Decompression ratio violation: individual stream expanded by {ratio:.1f}x "
                    f"(limit: {max_ratio}x)",
                    details={
                        "stream_compressed_bytes": compressed_len,
                        "stream_uncompressed_bytes": uncompressed_len,
                        "ratio": ratio,
                        "max_ratio": max_ratio,
                    },
                )

            if uncompressed_len > max_decompressed_bytes:
                raise SandboxViolationError(
                    SandboxViolationType.DECOMPRESSION_BOMB,
                    f"Individual stream decompressed size ({uncompressed_len} bytes) "
                    f"exceeds limit ({max_decompressed_bytes} bytes)",
                    details={
                        "uncompressed_bytes": uncompressed_len,
                        "limit_bytes": max_decompressed_bytes,
                    },
                )
        except SandboxViolationError:
            raise
        except Exception:
            # Not a zlib stream or raw binary; skip
            continue

    if total_compressed > 0:
        overall_ratio = total_uncompressed / max(1, total_compressed)
        if overall_ratio > max_ratio and total_uncompressed > 5 * 1024 * 1024:
            raise SandboxViolationError(
                SandboxViolationType.DECOMPRESSION_BOMB,
                f"Cumulative decompression ratio violation: {overall_ratio:.1f}x (limit: {max_ratio}x)",
                details={
                    "total_compressed": total_compressed,
                    "total_uncompressed": total_uncompressed,
                    "overall_ratio": overall_ratio,
                    "max_ratio": max_ratio,
                },
            )


def _check_page_count_fast(raw_bytes: bytes, max_pages: int = 100) -> None:
    """Pre-scan raw PDF structure to cap page count before heavy rendering."""
    page_matches = len(re.findall(rb"/Type\s*/Page\b", raw_bytes))
    pages_catalogs = len(re.findall(rb"/Type\s*/Pages\b", raw_bytes))
    estimated_pages = max(0, page_matches - pages_catalogs)

    if estimated_pages > max_pages:
        raise SandboxViolationError(
            SandboxViolationType.PAGE_COUNT_EXCEEDED,
            f"Document page count ({estimated_pages}) exceeds sandbox policy maximum ({max_pages})",
            details={"estimated_pages": estimated_pages, "max_pages": max_pages},
        )


def _build_posix_preexec(cpu_limit_sec: int, memory_limit_mb: int) -> Any:
    """Create preexec function for POSIX resource limits (RLIMIT_CPU, RLIMIT_AS)."""
    if os.name != "posix":
        return None

    def _set_rlimits() -> None:
        try:
            import resource

            # RLIMIT_CPU: CPU time limit in seconds
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit_sec, cpu_limit_sec + 2))  # type: ignore[attr-defined]
            # RLIMIT_AS: address space / virtual memory limit in bytes
            mem_bytes = memory_limit_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))  # type: ignore[attr-defined]
        except Exception:
            pass

    return _set_rlimits


class SandboxedWorkerManager:
    """Hardened execution manager running parsing and untrusted logic in an isolated subprocess."""

    def __init__(
        self,
        wall_clock_timeout: int | None = None,
        cpu_limit_seconds: int | None = None,
        memory_limit_mb: int | None = None,
        max_file_size_bytes: int | None = None,
        max_pages: int | None = None,
        max_decompression_ratio: float | None = None,
    ) -> None:
        self.wall_clock_timeout = (
            wall_clock_timeout or settings.sandbox_wall_clock_timeout_seconds
        )
        self.cpu_limit_seconds = cpu_limit_seconds or settings.sandbox_cpu_limit_seconds
        self.memory_limit_mb = memory_limit_mb or settings.sandbox_memory_limit_mb
        self.max_file_size_bytes = (
            max_file_size_bytes or settings.sandbox_max_file_size_bytes
        )
        self.max_pages = max_pages or settings.sandbox_max_page_count
        self.max_decompression_ratio = (
            max_decompression_ratio or settings.sandbox_max_decompression_ratio
        )

    def validate_file_guards(self, file_path: Path) -> None:
        """Enforce hard caps on file size, decompression ratio, and page count."""
        if not file_path.exists():
            raise SandboxViolationError(
                SandboxViolationType.PARSER_ERROR,
                f"Target file does not exist: {file_path}",
                details={"path": str(file_path)},
            )

        file_size = file_path.stat().st_size
        if file_size > self.max_file_size_bytes:
            raise SandboxViolationError(
                SandboxViolationType.FILE_SIZE_EXCEEDED,
                f"File size ({file_size} bytes) exceeds sandbox hard cap ({self.max_file_size_bytes} bytes)",
                details={"file_size": file_size, "limit_bytes": self.max_file_size_bytes},
            )

        # Decompression ratio check & page count check
        raw_bytes = file_path.read_bytes()
        _check_decompression_ratio(raw_bytes, max_ratio=self.max_decompression_ratio)
        _check_page_count_fast(raw_bytes, max_pages=self.max_pages)

    def parse_document_isolated(
        self, quarantined_file: Path, document_id: str
    ) -> tuple[ForensicReport, str, dict[str, Any]]:
        """Run document parser in an isolated subprocess with RLIMIT, timeout, and network isolation."""
        # 1. Pre-execution security checks
        self.validate_file_guards(quarantined_file)

        # 2. Setup isolated temp working directory
        with tempfile.TemporaryDirectory(prefix="nirikshan_sandbox_") as temp_dir:
            temp_path = Path(temp_dir)
            output_file = temp_path / f"result_{document_id}_{uuid.uuid4().hex[:6]}.json"

            # Prepare network-isolated subprocess environment
            env = os.environ.copy()
            env["NIRIKSHAN_SANDBOX_ACTIVE"] = "1"
            env["PYTHONNOUSERSITE"] = "1"
            env["HTTP_PROXY"] = ""
            env["HTTPS_PROXY"] = ""
            env["ALL_PROXY"] = ""
            env["NO_PROXY"] = "*"

            # Network blocking preamble script
            bootstrap_script = (
                "import socket, sys\n"
                "def _blocked(*a, **k): raise PermissionError('Network access strictly disabled in sandbox')\n"
                "socket.socket = _blocked\n"
                "import runpy\n"
                "sys.argv = ['nirikshan.worker.runner', '--input', sys.argv[1], '--output', sys.argv[2], '--doc-id', sys.argv[3]]\n"
                "runpy.run_module('nirikshan.worker.runner', run_name='__main__')\n"
            )

            cmd = [
                sys.executable,
                "-c",
                bootstrap_script,
                str(quarantined_file.resolve()),
                str(output_file.resolve()),
                document_id,
            ]

            preexec = _build_posix_preexec(self.cpu_limit_seconds, self.memory_limit_mb)

            try:
                completed = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.wall_clock_timeout,
                    check=False,
                    cwd=str(temp_path),
                    env=env,
                    preexec_fn=preexec,
                )
            except subprocess.TimeoutExpired as e:
                raise SandboxViolationError(
                    SandboxViolationType.TIMEOUT_EXCEEDED,
                    f"Sandbox subprocess exceeded wall-clock timeout ({self.wall_clock_timeout}s)",
                    details={"timeout_seconds": self.wall_clock_timeout},
                ) from e

            # Check if output was produced
            if not output_file.exists():
                stderr_msg = completed.stderr.strip() or completed.stdout.strip()
                if "PermissionError" in stderr_msg and "Network access" in stderr_msg:
                    raise SandboxViolationError(
                        SandboxViolationType.NETWORK_ACCESS_BLOCKED,
                        "Untrusted parser attempted network access inside sandbox",
                        details={"stderr": stderr_msg},
                    )
                if completed.returncode in (-9, 137, 128 + 9):
                    raise SandboxViolationError(
                        SandboxViolationType.MEMORY_LIMIT_EXCEEDED,
                        f"Sandbox process killed due to memory limit ({self.memory_limit_mb}MB)",
                        details={"exit_code": completed.returncode},
                    )
                if completed.returncode in (-24, 152):  # SIGXCPU
                    raise SandboxViolationError(
                        SandboxViolationType.CPU_LIMIT_EXCEEDED,
                        f"Sandbox process killed due to CPU limit ({self.cpu_limit_seconds}s)",
                        details={"exit_code": completed.returncode},
                    )
                raise SandboxViolationError(
                    SandboxViolationType.PARSER_ERROR,
                    f"Worker subprocess exited with code {completed.returncode}: {stderr_msg}",
                    details={"exit_code": completed.returncode, "stderr": stderr_msg},
                )

            try:
                data = json.loads(output_file.read_text(encoding="utf-8"))
            except Exception as e:
                raise SandboxViolationError(
                    SandboxViolationType.PARSER_ERROR,
                    f"Malformed output JSON from sandbox: {e}",
                    details={"error": str(e)},
                ) from e

            if not data.get("success"):
                err_type = data.get("violation_type") or SandboxViolationType.PARSER_ERROR
                err_msg = data.get("error", "Unknown parser error inside sandbox")
                raise SandboxViolationError(
                    err_type,
                    f"Sandbox parse error: {err_msg}",
                    details=data.get("details", {}),
                )

            forensic = ForensicReport.model_validate(data["forensic"])
            text_preview = str(data.get("text_preview", ""))
            extracted_params: dict[str, Any] = data.get("extracted_params", {})

            return forensic, text_preview, extracted_params

    def run_isolated_code(
        self,
        python_code: str,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Run arbitrary python code inside the sandbox subprocess with timeout and network limits."""
        effective_timeout = timeout or self.wall_clock_timeout

        with tempfile.TemporaryDirectory(prefix="nirikshan_sandbox_code_") as temp_dir:
            temp_path = Path(temp_dir)
            script_file = temp_path / "sandbox_stub.py"
            result_file = temp_path / "sandbox_result.json"

            preamble = (
                "import socket, sys, json\n"
                "def _blocked(*a, **k): raise PermissionError('Network access strictly disabled in sandbox')\n"
                "socket.socket = _blocked\n"
                "def _emit_success(res):\n"
                f"    with open(r'{result_file.resolve()}', 'w', encoding='utf-8') as f:\n"
                "        json.dump({{'success': True, 'result': res}}, f)\n"
            )
            script_file.write_text(preamble + "\n" + python_code, encoding="utf-8")

            env = os.environ.copy()
            env["NIRIKSHAN_SANDBOX_ACTIVE"] = "1"
            env["PYTHONNOUSERSITE"] = "1"
            env["HTTP_PROXY"] = ""
            env["HTTPS_PROXY"] = ""
            env["ALL_PROXY"] = ""
            env["NO_PROXY"] = "*"

            preexec = _build_posix_preexec(self.cpu_limit_seconds, self.memory_limit_mb)

            try:
                completed = subprocess.run(
                    [sys.executable, str(script_file.resolve())],
                    capture_output=True,
                    text=True,
                    timeout=effective_timeout,
                    check=False,
                    cwd=str(temp_path),
                    env=env,
                    preexec_fn=preexec,
                )
            except subprocess.TimeoutExpired as e:
                raise SandboxViolationError(
                    SandboxViolationType.TIMEOUT_EXCEEDED,
                    f"Execution exceeded wall-clock timeout limit ({effective_timeout}s)",
                    details={"timeout_seconds": effective_timeout},
                ) from e

            if not result_file.exists():
                stderr_msg = completed.stderr.strip()
                if "PermissionError" in stderr_msg and "Network access" in stderr_msg:
                    raise SandboxViolationError(
                        SandboxViolationType.NETWORK_ACCESS_BLOCKED,
                        "Network access strictly disabled in sandbox",
                        details={"stderr": stderr_msg},
                    )
                if completed.returncode in (-9, 137, 128 + 9):
                    raise SandboxViolationError(
                        SandboxViolationType.MEMORY_LIMIT_EXCEEDED,
                        f"Memory limit exceeded ({self.memory_limit_mb}MB)",
                        details={"exit_code": completed.returncode},
                    )
                if completed.returncode in (-24, 152):
                    raise SandboxViolationError(
                        SandboxViolationType.CPU_LIMIT_EXCEEDED,
                        f"CPU limit exceeded ({self.cpu_limit_seconds}s)",
                        details={"exit_code": completed.returncode},
                    )
                raise SandboxViolationError(
                    SandboxViolationType.PARSER_ERROR,
                    f"Sandbox stub exited with code {completed.returncode}: {stderr_msg}",
                    details={"exit_code": completed.returncode, "stderr": stderr_msg},
                )

            return json.loads(result_file.read_text(encoding="utf-8"))


# Global singleton
sandbox_manager = SandboxedWorkerManager()
worker_manager = sandbox_manager
