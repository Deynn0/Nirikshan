"""PDF authoring tool signature detector.

Extracts /Producer, /Creator, and /Application metadata fields and cross-checks
them against:
1. A known-safe whitelist (government portals, standard office tools).
2. A suspicious-tool blacklist (online converters, editing services that
   frequently appear in forged documents).
3. Version string extraction to detect downgraded tools (e.g. Acrobat 5.x
   is widely used for forgery due to weak encryption).

Also checks XMP metadata for tool fingerprints.

All findings are at trust level STRUCTURAL_FORENSIC.
"""

from __future__ import annotations

import re
from pathlib import Path

from nirikshan.forensics.models import FindingCategory, FindingSeverity, ForensicFinding
from nirikshan.ingest.models import ParsedDocument

_DETECTOR = "tool_signature_detector"

# Online / cloud PDF editors associated with forgery
_SUSPICIOUS_TOOLS = [
    "ilovepdf",
    "smallpdf",
    "sejda",
    "pdf2doc",
    "pdf24",
    "pdfcandy",
    "pdfbear",
    "pdf.io",
    "sodapdf",
    "pdffiller",
    "docfly",
    "pdfpro",
    "pdfescape",
    "formswift",
    "jotform",
    "signalite",
]

# Trusted government / standard tools
_TRUSTED_TOOLS = [
    "digilocker",
    "esign india",
    "nsdl",
    "cdsl",
    "meity",
    "nic ",
    "national informatics",
    "microsoft word",
    "microsoft office",
    "libreoffice",
    "openoffice",
    "apache fop",
    "reportlab",
    "ghostscript",
    "wkhtmltopdf",
    "pdflatex",
    "xelatex",
    "lualatex",
    "acrobat",  # Adobe Acrobat (standard)
    "pdf creator",
]

# Very old Acrobat versions used for forgery due to weak security
_OLD_ACROBAT_RE = re.compile(r"acrobat\s+(?:distiller\s+)?(\d+)\.", re.I)


def _extract_xmp_tools(path: Path) -> list[str]:
    """Extract tool strings from raw XMP metadata in the PDF bytes."""
    tools: list[str] = []
    try:
        raw = path.read_bytes()
        # XMP is embedded in raw XML; look for xmp:CreatorTool
        m = re.search(rb"<xmp:CreatorTool>([^<]{0,200})</xmp:CreatorTool>", raw)
        if m:
            tools.append(m.group(1).decode("utf-8", errors="ignore").strip())
        m2 = re.search(rb"<xmpMM:InstanceID>([^<]{0,200})</xmpMM:InstanceID>", raw)
        if m2:
            tools.append(m2.group(1).decode("utf-8", errors="ignore").strip())
    except Exception:
        pass
    return tools


def detect(doc: ParsedDocument) -> list[ForensicFinding]:
    findings: list[ForensicFinding] = []

    producer = doc.metadata.producer or ""
    creator = doc.metadata.creator or ""
    xmp_tools = _extract_xmp_tools(doc.file_path)

    all_tool_strings = [s for s in [producer, creator] + xmp_tools if s]

    for tool_str in all_tool_strings:
        tool_lower = tool_str.lower()

        # ---- Check suspicious tools ----
        for suspicious in _SUSPICIOUS_TOOLS:
            if suspicious in tool_lower:
                findings.append(
                    ForensicFinding(
                        detector=_DETECTOR,
                        category=FindingCategory.TOOL_SIGNATURE,
                        severity=FindingSeverity.HIGH,
                        title=f"Suspicious PDF Editing Tool: '{tool_str}'",
                        description=(
                            f"The PDF was produced or last modified by '{tool_str}', "
                            f"which is an online/cloud PDF editor. These tools are "
                            f"frequently used to alter official documents. "
                            f"Regulatory submissions must originate from recognized "
                            f"government portals or standard authoring software."
                        ),
                        evidence={"tool_string": tool_str, "matched_pattern": suspicious},
                    )
                )

        # ---- Check for old/vulnerable Acrobat versions ----
        m = _OLD_ACROBAT_RE.search(tool_str)
        if m:
            version = int(m.group(1))
            if version <= 7:
                findings.append(
                    ForensicFinding(
                        detector=_DETECTOR,
                        category=FindingCategory.TOOL_SIGNATURE,
                        severity=FindingSeverity.MEDIUM,
                        title=f"Old Acrobat Version Detected: v{version}.x",
                        description=(
                            f"The PDF was produced by Adobe Acrobat v{version}.x "
                            f"({tool_str}). Acrobat versions ≤7 have known weak encryption "
                            f"and are frequently used in document forgery workflows."
                        ),
                        evidence={"tool_string": tool_str, "acrobat_version": version},
                    )
                )

    # ---- Producer/Creator both absent ----
    if not producer and not creator:
        findings.append(
            ForensicFinding(
                detector=_DETECTOR,
                category=FindingCategory.TOOL_SIGNATURE,
                severity=FindingSeverity.MEDIUM,
                title="Missing PDF Producer and Creator Metadata",
                description=(
                    "The PDF lacks both /Producer and /Creator metadata fields. "
                    "Legitimate government-issued documents always embed these fields. "
                    "Missing metadata may indicate the fields were deliberately stripped."
                ),
                evidence={"producer": producer, "creator": creator},
            )
        )

    # ---- Info observation when trusted ----
    if all_tool_strings:
        is_trusted = any(
            trusted in " ".join(all_tool_strings).lower()
            for trusted in _TRUSTED_TOOLS
        )
        if is_trusted:
            findings.append(
                ForensicFinding(
                    detector=_DETECTOR,
                    category=FindingCategory.TOOL_SIGNATURE,
                    severity=FindingSeverity.INFO,
                    title=f"Recognized PDF Authoring Tool: '{all_tool_strings[0]}'",
                    description="The PDF producer/creator matches a recognized institutional tool.",
                    evidence={"tool_strings": all_tool_strings},
                )
            )

    return findings
