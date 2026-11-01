"""Forensic scan runner — entry point for nirikshan.forensics.scan.

Usage (CLI):
    python -m nirikshan.forensics.scan <file.pdf> [--json] [--no-ocr] [--no-raster]

Usage (Python):
    from nirikshan.forensics.scan import scan_pdf
    report = scan_pdf(Path("file.pdf"))
    print(report.as_dict())

Runs all detectors in sequence:
  1. revision_detector
  2. font_detector
  3. whiteout_detector
  4. tool_signature_detector
  5. seal_detector

Returns a ScanReport with all ForensicFindings consolidated.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from nirikshan.forensics import (
    font_detector,
    pdf_signature_detector,
    revision_detector,
    seal_detector,
    tool_signature_detector,
    whiteout_detector,
)
from nirikshan.forensics.models import ScanReport
from nirikshan.ingest.pipeline import ingest_pdf

log = logging.getLogger(__name__)


def scan_pdf(
    path: Path,
    *,
    enable_raster: bool = True,
    enable_ocr: bool = True,
) -> ScanReport:
    """Run the full forensic scan pipeline on a PDF file.

    Args:
        path: Path to the PDF file.
        enable_raster: Rasterize pages for visual detectors.
        enable_ocr: Run OCR on scanned pages.

    Returns:
        ScanReport with all findings from all detectors.
    """
    log.info("Starting forensic scan: %s", path.name)

    # 1. Ingest
    doc = ingest_pdf(path, enable_raster=enable_raster, enable_ocr=enable_ocr)

    # 2. Run all detectors
    all_findings = []

    for detector_mod in [
        revision_detector,
        font_detector,
        whiteout_detector,
        tool_signature_detector,
        seal_detector,
        pdf_signature_detector,
    ]:
        try:
            findings = detector_mod.detect(doc)
            log.debug("%s: %d finding(s)", detector_mod.__name__, len(findings))
            all_findings.extend(findings)
        except Exception as exc:
            log.error("Detector %s failed: %s", detector_mod.__name__, exc, exc_info=True)

    report = ScanReport(
        file_path=str(path.resolve()),
        sha256=doc.metadata.sha256_hash,
        page_count=len(doc.pages),
        findings=all_findings,
    )

    log.info(
        "Scan complete: %d finding(s) [CRITICAL=%d, HIGH=%d]",
        len(all_findings),
        report.critical_count,
        report.high_count,
    )
    return report


def main() -> None:
    """CLI entry point: python -m nirikshan.forensics.scan file.pdf [--json]"""
    parser = argparse.ArgumentParser(
        prog="python -m nirikshan.forensics.scan",
        description="Nirikshan PDF forensic scanner",
    )
    parser.add_argument("file", type=Path, help="PDF file to scan")
    parser.add_argument("--json", action="store_true", help="Output JSON (default: human-readable)")
    parser.add_argument("--no-raster", action="store_true", help="Skip page rasterization")
    parser.add_argument("--no-ocr", action="store_true", help="Skip OCR fallback")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(name)s %(levelname)s: %(message)s",
    )

    pdf_path: Path = args.file
    if not pdf_path.exists():
        print(f"ERROR: File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    if not str(pdf_path).lower().endswith(".pdf"):
        print(f"WARNING: File does not have .pdf extension: {pdf_path}", file=sys.stderr)

    report = scan_pdf(
        pdf_path,
        enable_raster=not args.no_raster,
        enable_ocr=not args.no_ocr,
    )

    if args.json:
        print(json.dumps(report.as_dict(), indent=2, ensure_ascii=False))
    else:
        _print_human_report(report)


def _print_human_report(report: ScanReport) -> None:
    """Print a human-readable scan report to stdout."""
    sev_icons = {
        "CRITICAL": "[CRITICAL]",
        "HIGH":     "[HIGH]    ",
        "MEDIUM":   "[MEDIUM]  ",
        "LOW":      "[LOW]     ",
        "INFO":     "[INFO]    ",
    }
    print(f"\n{'='*70}")
    print("  NIRIKSHAN FORENSIC SCAN REPORT")
    print(f"{'='*70}")
    print(f"  File    : {report.file_path}")
    print(f"  SHA-256 : {report.sha256}")
    print(f"  Pages   : {report.page_count}")
    print(f"  Findings: {len(report.findings)} total | CRITICAL={report.critical_count} | HIGH={report.high_count}")
    print(f"{'='*70}\n")

    if not report.findings:
        print("  [OK] No forensic anomalies detected.\n")
        return

    for i, f in enumerate(report.findings, 1):
        icon = sev_icons.get(f.severity, "?  ")
        page_str = f"[Page {f.page}]" if f.page else "[Doc]"
        print(f"  {i:02d}. {icon} {page_str} {f.title}")
        print(f"      Detector : {f.detector}")
        print(f"      Category : {f.category}")
        print(f"      {f.description[:180]}")
        if f.bbox:
            print(f"      BBox(pts): {f.bbox}")
        print()


if __name__ == "__main__":
    main()
