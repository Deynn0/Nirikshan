"""Standalone worker CLI runner for untrusted document parsing in an isolated process."""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
import uuid
from pathlib import Path

from nirikshan.crypto.storage import encrypted_storage
from nirikshan.parsers.pdf_parser import pdf_analyzer
from nirikshan.sandbox import (
    SandboxViolationError,
    SandboxViolationType,
    _check_decompression_ratio,
    _check_page_count_fast,
)


def main() -> int:
    """Entry point for sandboxed worker subprocess."""
    parser = argparse.ArgumentParser(description="Isolated Untrusted Document Parser")
    parser.add_argument("--input", required=True, help="Path to quarantined input file or envelope")
    parser.add_argument("--output", required=True, help="Path to write JSON inspection results")
    parser.add_argument("--doc-id", required=True, help="Document ID")

    args = parser.parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        sys.stderr.write(f"File not found: {input_path}\n")
        return 1

    temp_decrypted_path: Path | None = None
    target_parse_path = input_path

    try:
        # Check if input is an encrypted envelope (.enc or .enc.json)
        is_envelope = (
            input_path.name.endswith(".enc.json")
            or input_path.name.endswith(".enc")
            or '"wrapped_dek_b64"' in input_path.read_text(encoding="utf-8", errors="ignore")[:300]
        )

        if is_envelope:
            # Transparent decrypt in the sandbox only!
            decrypted_bytes = encrypted_storage.decrypt_document(input_path, is_sandbox=True)
            # Check decompression ratio & page count on the decrypted bytes
            _check_decompression_ratio(decrypted_bytes)
            _check_page_count_fast(decrypted_bytes)

            temp_decrypted_path = Path.cwd() / f"decrypted_{args.doc_id}_{uuid.uuid4().hex[:6]}.pdf"
            temp_decrypted_path.write_bytes(decrypted_bytes)
            target_parse_path = temp_decrypted_path

        forensic, text_preview, extracted_params = pdf_analyzer.analyze_file(
            target_parse_path, args.doc_id
        )
        result = {
            "success": True,
            "forensic": forensic.model_dump(mode="json"),
            "text_preview": text_preview,
            "extracted_params": extracted_params,
        }
        output_path.write_text(json.dumps(result), encoding="utf-8")
        return 0
    except SandboxViolationError as sve:
        error_result = {
            "success": False,
            "violation_type": sve.violation_type,
            "error": sve.message,
            "details": sve.details,
        }
        output_path.write_text(json.dumps(error_result), encoding="utf-8")
        return 2
    except Exception as e:
        error_result = {
            "success": False,
            "violation_type": SandboxViolationType.PARSER_ERROR,
            "error": str(e),
            "error_type": type(e).__name__,
        }
        output_path.write_text(json.dumps(error_result), encoding="utf-8")
        return 2
    finally:
        if temp_decrypted_path and temp_decrypted_path.exists():
            with contextlib.suppress(OSError):
                temp_decrypted_path.unlink()


if __name__ == "__main__":
    sys.exit(main())
