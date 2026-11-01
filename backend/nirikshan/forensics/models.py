"""Shared Finding dataclass used by all forensic detectors.

Every detector returns list[ForensicFinding].  The scan runner in
nirikshan.forensics.scan collects them all into a ScanReport.

Trust levels:
  - STRUCTURAL_FORENSIC: automated analysis, no human review
  - RECORD: verified external record (e.g., xref structure cross-check)

The forensic detectors intentionally produce STRUCTURAL_FORENSIC findings
unless overridden by a sub-detector that has cross-verified with an
external source.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class FindingSeverity(StrEnum):
    CRITICAL = "CRITICAL"      # definite tamper evidence
    HIGH = "HIGH"              # strong signal, needs manual review
    MEDIUM = "MEDIUM"          # moderate anomaly
    LOW = "LOW"                # informational / weak signal
    INFO = "INFO"              # metadata observation, no risk


class FindingCategory(StrEnum):
    REVISION = "REVISION"          # incremental update / prev-chain
    FONT = "FONT"                  # font inconsistency
    WHITEOUT = "WHITEOUT"          # white rectangle overlay
    TOOL_SIGNATURE = "TOOL_SIGNATURE"  # /Producer, /Creator tell-tale
    SEAL = "SEAL"                  # stamp / seal forensics
    METADATA = "METADATA"          # date, author anomaly
    JAVASCRIPT = "JAVASCRIPT"      # dangerous embedded code
    SIGNATURE = "SIGNATURE"        # digital signature / PAdES / CMS forensics


@dataclass
class ForensicFinding:
    """Single forensic observation from any detector."""

    detector: str                  # module name, e.g. "revision_detector"
    category: FindingCategory
    severity: FindingSeverity
    title: str
    description: str
    page: int | None = None        # 1-based, None = document-level
    bbox: dict[str, float] | None = None  # {x0,y0,x1,y1} in PDF points
    evidence: dict[str, object] = field(default_factory=dict)
    trust_level: str = "STRUCTURAL_FORENSIC"

    def as_dict(self) -> dict[str, object]:
        return {
            "detector": self.detector,
            "category": self.category,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "page": self.page,
            "bbox": self.bbox,
            "evidence": self.evidence,
            "trust_level": self.trust_level,
        }


@dataclass
class ScanReport:
    """Aggregate report produced by nirikshan.forensics.scan."""

    file_path: str
    sha256: str
    page_count: int
    findings: list[ForensicFinding] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == FindingSeverity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == FindingSeverity.HIGH)

    def as_dict(self) -> dict[str, object]:
        return {
            "file_path": self.file_path,
            "sha256": self.sha256,
            "page_count": self.page_count,
            "total_findings": len(self.findings),
            "critical": self.critical_count,
            "high": self.high_count,
            "findings": [f.as_dict() for f in self.findings],
        }
