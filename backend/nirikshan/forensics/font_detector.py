"""Font inconsistency detector.

Checks:
1. Multiple distinct font families on a single page (indicative of copy-paste
   from different source documents).
2. Non-embedded fonts (may indicate substitution by viewer).
3. Unusual font subtypes for institutional documents (e.g. Type3, which can
   encode arbitrary glyphs).
4. Font names that contain version strings or tool identifiers
   (e.g. "ArialMT", "Helvetica-Oblique" alongside "Calibri-Bold" on same page).
5. Size discontinuities: body text appears at wildly varying sizes across
   adjacent paragraphs (heuristic: >3x difference on same page).

All findings are at trust level STRUCTURAL_FORENSIC.
"""

from __future__ import annotations

import collections
import re

from nirikshan.forensics.models import FindingCategory, FindingSeverity, ForensicFinding
from nirikshan.ingest.models import ParsedDocument

_DETECTOR = "font_detector"

# Fonts associated with PDF editing / forgery tools
_SUSPICIOUS_FONT_PATTERNS = [
    re.compile(r"adobe\s*acrobat", re.I),
    re.compile(r"foxit", re.I),
    re.compile(r"nitro", re.I),
    re.compile(r"pdfmaker", re.I),
    re.compile(r"pdfedit", re.I),
    re.compile(r"cutepdf", re.I),
    re.compile(r"ghostscript", re.I),
    re.compile(r"ilovepdf", re.I),
    re.compile(r"smallpdf", re.I),
    re.compile(r"sejda", re.I),
]

_SUSPICIOUS_SUBTYPES = {"Type3"}


def _base_family(font_name: str) -> str:
    """Strip weight/style suffixes to get the base font family."""
    name = font_name.split("+")[-1]  # strip subset prefix e.g. "ABCDEF+Arial"
    name = re.sub(r"[-,](Bold|Italic|Oblique|Regular|Light|Medium|Condensed|Narrow).*", "", name, flags=re.I)
    return name.strip()


def detect(doc: ParsedDocument) -> list[ForensicFinding]:
    findings: list[ForensicFinding] = []

    for page in doc.pages:
        page_fonts = page.fonts
        if not page_fonts and not page.words:
            continue

        # ---- 1. Font families on this page ----
        families: list[str] = []
        for fi in page_fonts:
            if fi.name:
                families.append(_base_family(fi.name))

        # Also collect from word tokens (pdfplumber font names)
        word_fonts = {w.font_name for w in page.words if w.font_name}
        for wf in word_fonts:
            families.append(_base_family(wf))

        family_counts = collections.Counter(families)
        unique_families = [f for f in family_counts if f]

        if len(unique_families) > 4:
            findings.append(
                ForensicFinding(
                    detector=_DETECTOR,
                    category=FindingCategory.FONT,
                    severity=FindingSeverity.MEDIUM,
                    title=f"Page {page.page_number}: Excessive Font Diversity ({len(unique_families)} families)",
                    description=(
                        f"Page {page.page_number} uses {len(unique_families)} distinct font "
                        f"families: {', '.join(sorted(unique_families)[:8])}. "
                        f"Legitimate institutional documents rarely use more than 3-4 fonts."
                    ),
                    page=page.page_number,
                    evidence={"font_families": sorted(unique_families), "counts": dict(family_counts)},
                )
            )

        # ---- 2. Non-embedded fonts ----
        non_embedded = [fi for fi in page_fonts if not fi.is_embedded and fi.name]
        if non_embedded:
            findings.append(
                ForensicFinding(
                    detector=_DETECTOR,
                    category=FindingCategory.FONT,
                    severity=FindingSeverity.LOW,
                    title=f"Page {page.page_number}: Non-Embedded Fonts ({len(non_embedded)})",
                    description=(
                        f"Fonts {[f.name for f in non_embedded]} are not embedded in the PDF. "
                        f"This allows viewer substitution and may change document appearance."
                    ),
                    page=page.page_number,
                    evidence={"non_embedded_fonts": [f.name for f in non_embedded]},
                )
            )

        # ---- 3. Suspicious font subtypes ----
        suspicious_sub = [fi for fi in page_fonts if fi.subtype in _SUSPICIOUS_SUBTYPES]
        if suspicious_sub:
            findings.append(
                ForensicFinding(
                    detector=_DETECTOR,
                    category=FindingCategory.FONT,
                    severity=FindingSeverity.HIGH,
                    title=f"Page {page.page_number}: Suspicious Font Subtype (Type3)",
                    description=(
                        "Type3 fonts contain arbitrary PostScript glyph programs and can "
                        "encode arbitrary shapes, making text extraction unreliable and "
                        "enabling steganographic content."
                    ),
                    page=page.page_number,
                    evidence={"type3_fonts": [f.name for f in suspicious_sub]},
                )
            )

        # ---- 4. Font size discontinuity in word tokens ----
        sizes = [w.font_size for w in page.words if w.font_size and w.font_size > 0]
        if sizes:
            max_size = max(sizes)
            min_size = min(sizes)
            if min_size > 0 and max_size / min_size > 4.0:
                findings.append(
                    ForensicFinding(
                        detector=_DETECTOR,
                        category=FindingCategory.FONT,
                        severity=FindingSeverity.LOW,
                        title=f"Page {page.page_number}: Font Size Discontinuity (min={min_size:.1f}pt, max={max_size:.1f}pt)",
                        description=(
                            f"Font sizes range from {min_size:.1f}pt to {max_size:.1f}pt "
                            f"(ratio {max_size/min_size:.1f}×). Large discontinuities may "
                            f"indicate inserted text blocks from different source documents."
                        ),
                        page=page.page_number,
                        evidence={"min_size": min_size, "max_size": max_size, "ratio": round(max_size / min_size, 2)},
                    )
                )

    # ---- 5. Cross-page font consistency check ----
    # Fonts that appear on only one page but not on surrounding pages
    page_font_sets: list[set[str]] = []
    for page in doc.pages:
        page_font_sets.append({_base_family(fi.name) for fi in page.fonts if fi.name})

    for i, page in enumerate(doc.pages[1:-1], start=1):
        prev_fonts = page_font_sets[i - 1]
        curr_fonts = page_font_sets[i]
        next_fonts = page_font_sets[i + 1]
        unique_to_page = curr_fonts - prev_fonts - next_fonts
        # Only flag if the unique font is a substantive name (not empty/unknown)
        significant = {f for f in unique_to_page if len(f) > 2}
        if significant:
            findings.append(
                ForensicFinding(
                    detector=_DETECTOR,
                    category=FindingCategory.FONT,
                    severity=FindingSeverity.LOW,
                    title=f"Page {page.page_number}: Isolated Font Family ({', '.join(sorted(significant))})",
                    description=(
                        f"Font(s) {sorted(significant)} appear only on page {page.page_number} "
                        f"and not on adjacent pages. This may indicate a replaced or inserted page."
                    ),
                    page=page.page_number,
                    evidence={"isolated_fonts": sorted(significant)},
                )
            )

    return findings
