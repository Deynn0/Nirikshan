"""Cross-application fraud detectors for Nirikshan scrutiny engine.

Detectors implemented:
1. Ghost Faculty: Same faculty hash declared full-time at 2+ institutions with overlapping periods.
2. Certificate Sharing: Same Fire NOC / land registration number across unrelated institutions.
3. Photo Reuse: Identical or near-identical (hamming distance threshold) lab/campus photos across applicants.
4. Seal Reuse: Same seal perceptual hash across different issuing authorities.
"""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from nirikshan.config import settings
from nirikshan.fraud.hasher import hamming_distance
from nirikshan.fraud.models import EntityType
from nirikshan.schemas.citation import HandbookCitation
from nirikshan.schemas.finding import Finding, VerificationStatus
from nirikshan.trust.ladder import EvidenceItem, TrustLevel

logger = logging.getLogger(__name__)


def parse_academic_years(period_str: str) -> set[int]:
    """Extract individual calendar years from period representations.

    Supports:
      '2024-2025' -> {2024, 2025}
      '2024-25'   -> {2024, 2025}
      '2024'      -> {2024}
      '2022-2024' -> {2022, 2023, 2024}
    """
    years: set[int] = set()
    if not period_str:
        return years

    # Look for 4-digit years
    matches = re.findall(r"\b(20\d\d)\b", str(period_str))
    if len(matches) == 1:
        # Check for 2-digit suffix like 2024-25
        y1 = int(matches[0])
        years.add(y1)
        suffix = re.search(r"20\d\d[-/](\d{2})\b", str(period_str))
        if suffix:
            y2 = int(f"20{suffix.group(1)}")
            years.add(y2)
    elif len(matches) >= 2:
        y1 = int(matches[0])
        y2 = int(matches[1])
        if y1 <= y2:
            years.update(range(y1, y2 + 1))
        else:
            years.update([y1, y2])
    return years


def check_periods_overlap(periods_a: list[str], periods_b: list[str]) -> bool:
    """Return True if any declared academic period or year between two sets overlaps.

    If either set is empty, returns True by default (assumed active inspection session).
    """
    if not periods_a or not periods_b:
        return True

    years_a: set[int] = set()
    for p in periods_a:
        years_a.update(parse_academic_years(p))

    years_b: set[int] = set()
    for p in periods_b:
        years_b.update(parse_academic_years(p))

    # If parsing found specific years in both, compare intersection
    if years_a and years_b:
        return len(years_a & years_b) > 0

    # Fallback to direct string matching
    set_a = {str(p).strip().lower() for p in periods_a}
    set_b = {str(p).strip().lower() for p in periods_b}
    return len(set_a & set_b) > 0


def normalize_authority_name(auth: str) -> str:
    """Normalize issuing authority name for comparison."""
    if not auth:
        return ""
    # Strip common stopwords
    clean = re.sub(r"[^\w\s]", " ", auth.lower())
    words = [w for w in clean.split() if w not in {"the", "of", "department", "dept", "office", "and", "for"}]
    return " ".join(words)


class GhostFacultyDetector:
    """Detects simultaneous full-time appointment of the same faculty across institutions."""

    RULE_ID = "AICTE-FRAUD-GHOST-FACULTY"
    RULE_NAME = "Ghost Faculty: Simultaneous Full-Time Appointment"

    @classmethod
    def detect(cls, applications: list[dict[str, Any]]) -> list[Finding]:
        findings: list[Finding] = []

        # Group faculty usages: faculty_hash -> list of {dossier_id, inst_name, metadata}
        faculty_map: dict[str, list[dict[str, Any]]] = {}

        for app in applications:
            d_id = app["dossier_id"]
            inst = app.get("institution_name", d_id)
            for ent in app.get("entities", []):
                if ent.entity_type == EntityType.FACULTY:
                    fac_hash = ent.entity_value
                    meta = ent.metadata or {}
                    faculty_map.setdefault(fac_hash, []).append({
                        "dossier_id": d_id,
                        "institution_name": inst,
                        "employment_type": str(meta.get("employment_type", "FULL_TIME")).upper(),
                        "periods": meta.get("periods", ["2024-2025"]),
                        "faculty_name": meta.get("faculty_name", "Unknown"),
                        "designation": meta.get("designation", "Faculty"),
                        "label": ent.label,
                    })

        for fac_hash, usages in faculty_map.items():
            # Deduplicate by dossier_id (same institution declaring multiple times is not cross-application fraud)
            unique_dossiers = {u["dossier_id"] for u in usages}
            if len(unique_dossiers) < 2:
                continue

            # Check for multiple FULL_TIME declarations with overlapping periods
            full_time_usages = [u for u in usages if "FULL" in u["employment_type"]]
            if len({u["dossier_id"] for u in full_time_usages}) < 2:
                continue

            # Compare pairs for period overlap
            conflicts: set[tuple[str, str]] = set()
            overlapping_usages: list[dict[str, Any]] = []

            for i, u1 in enumerate(full_time_usages):
                for u2 in full_time_usages[i + 1 :]:
                    if u1["dossier_id"] != u2["dossier_id"] and check_periods_overlap(
                        u1["periods"], u2["periods"]
                    ):
                        pair = (min(u1["dossier_id"], u2["dossier_id"]), max(u1["dossier_id"], u2["dossier_id"]))
                        conflicts.add(pair)
                        if u1 not in overlapping_usages:
                            overlapping_usages.append(u1)
                        if u2 not in overlapping_usages:
                            overlapping_usages.append(u2)

            if not conflicts:
                continue

            involved_ids = sorted({u["dossier_id"] for u in overlapping_usages})
            involved_insts = [f"{u['institution_name']} ({u['dossier_id']})" for u in overlapping_usages]

            evidence_list: list[EvidenceItem] = []
            for u in overlapping_usages:
                evidence_list.append(
                    EvidenceItem(
                        evidence_id=f"ev-ghost-{u['dossier_id']}-{fac_hash[:8]}",
                        trust_level=TrustLevel.RECORD,
                        source_type="Faculty Master List",
                        description=(
                            f"Full-time appointment declared at {u['institution_name']} "
                            f"(Designation: {u['designation']}, Periods: {', '.join(u['periods'])})"
                        ),
                        raw_value={"salted_hash": fac_hash, "periods": u["periods"]},
                        source_document_id=u["dossier_id"],
                        source_document_name=u["institution_name"],
                        verification_method="SALTED_HASH_TEMPORAL_INTERSECTION",
                        is_self_attested=False,
                        is_tampered=False,
                    )
                )

            display_name = overlapping_usages[0].get("faculty_name", "Faculty Member")
            f = Finding(
                finding_id=f"fnd-ghost-{uuid.uuid4().hex[:8]}",
                rule_id=cls.RULE_ID,
                rule_name=cls.RULE_NAME,
                category="Faculty Integrity",
                status=VerificationStatus.FLAGGED_TAMPER,
                summary=(
                    f"Ghost Faculty Detected: {display_name} (Salted Hash: {fac_hash[:8]}...) "
                    f"declared as full-time at {len(involved_ids)} distinct institutions simultaneously."
                ),
                details=(
                    f"Cross-application scrutiny revealed that faculty member (HMAC-SHA256 salted hash: {fac_hash}) "
                    f"is concurrently declared as regular full-time faculty with overlapping academic periods at: "
                    f"{', '.join(involved_insts)}. Under AICTE APH regulations, full-time faculty cannot hold "
                    f"concurrent full-time positions at another technical institution."
                ),
                handbook_citation=HandbookCitation(
                    handbook="AICTE Approval Process Handbook 2024-2027",
                    clause="Clause 4.3 & Appendix 7",
                    page=104,
                    edition="2024-2027",
                ),
                evidence_list=evidence_list,
                advisory_notes=[
                    f"Involved Application IDs: {', '.join(involved_ids)}",
                    "Aadhaar/PAN verified via deterministic salted HMAC-SHA256 hash. Plaintext identity was never logged.",
                    "Mandatory physical Biometric verification and salary disbursement bank audit recommended.",
                ],
            )
            findings.append(f)

        return findings


class CertificateSharingDetector:
    """Detects reuse of Fire NOC or Land Registration deeds across unrelated institutions."""

    RULE_ID = "AICTE-FRAUD-CERT-SHARING"
    RULE_NAME = "Certificate Sharing: Cross-Institution Document Recycling"

    @classmethod
    def detect(cls, applications: list[dict[str, Any]]) -> list[Finding]:
        findings: list[Finding] = []

        cert_map: dict[str, list[dict[str, Any]]] = {}

        for app in applications:
            d_id = app["dossier_id"]
            inst = app.get("institution_name", d_id)
            parent_trust = app.get("parent_trust") or app.get("extracted_params", {}).get("parent_trust")

            for ent in app.get("entities", []):
                if ent.entity_type in (EntityType.CERTIFICATE, EntityType.LAND_REG):
                    val = ent.entity_value
                    cert_map.setdefault(val, []).append({
                        "dossier_id": d_id,
                        "institution_name": inst,
                        "parent_trust": parent_trust,
                        "entity_type": ent.entity_type.value,
                        "entity_id": ent.entity_id,
                        "label": ent.label,
                        "metadata": ent.metadata or {},
                    })

        for val, usages in cert_map.items():
            unique_dossiers = {u["dossier_id"] for u in usages}
            if len(unique_dossiers) < 2:
                continue

            # Check if all institutions share the same parent trust and allow shared campus
            if settings.fraud_allow_shared_parent_trust:
                trusts = {u["parent_trust"] for u in usages if u.get("parent_trust")}
                # If all have the exact same parent trust, treat as sister institution
                if len(trusts) == 1 and len(trusts) == len(usages):
                    continue

            involved_ids = sorted(unique_dossiers)
            inst_list = [f"{u['institution_name']} ({u['dossier_id']})" for u in usages]
            ent_type = usages[0]["entity_type"]

            evidence_list: list[EvidenceItem] = []
            for u in usages:
                evidence_list.append(
                    EvidenceItem(
                        evidence_id=f"ev-cert-{u['dossier_id']}-{val[:8]}",
                        trust_level=TrustLevel.RECORD,
                        source_type="Statutory Certificate / Land Record",
                        description=f"{u['label']} submitted for regulatory compliance at {u['institution_name']}",
                        raw_value={"number": val, "entity_type": ent_type},
                        source_document_id=u["dossier_id"],
                        source_document_name=u["institution_name"],
                        verification_method="EXACT_STATUTORY_RECORD_INTERSECTION",
                        is_self_attested=False,
                        is_tampered=False,
                    )
                )

            type_name = "Fire NOC" if ent_type == EntityType.CERTIFICATE.value else "Land Registration Deed"
            f = Finding(
                finding_id=f"fnd-cert-{uuid.uuid4().hex[:8]}",
                rule_id=cls.RULE_ID,
                rule_name=cls.RULE_NAME,
                category="Infrastructure Integrity",
                status=VerificationStatus.FLAGGED_TAMPER,
                summary=(
                    f"Recycled {type_name} Detected: Statutory number '{val}' shared across "
                    f"{len(involved_ids)} unrelated institutions."
                ),
                details=(
                    f"The identical statutory document number '{val}' ({type_name}) was submitted by "
                    f"multiple independent institutions: {', '.join(inst_list)}. Under AICTE APH Chapter 5, "
                    f"statutory safety certificates and land title deeds must be exclusive to the institution's "
                    f"designated approved campus."
                ),
                handbook_citation=HandbookCitation(
                    handbook="AICTE Approval Process Handbook 2024-2027",
                    clause="Clause 5.1 & Clause 2.4",
                    page=48,
                    edition="2024-2027",
                ),
                evidence_list=evidence_list,
                advisory_notes=[
                    f"Involved Application IDs: {', '.join(involved_ids)}",
                    "Verify if institutions operate on a legally approved integrated shared campus under Clause 2.15.",
                ],
            )
            findings.append(f)

        return findings


class PhotoReuseDetector:
    """Detects identical or near-identical lab and campus photos across applicants."""

    RULE_ID = "AICTE-FRAUD-PHOTO-REUSE"
    RULE_NAME = "Photo Reuse: Recycled Laboratory/Campus Photographs"

    @classmethod
    def detect(
        cls,
        applications: list[dict[str, Any]],
        threshold: int | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        max_dist = threshold if threshold is not None else settings.fraud_photo_hamming_threshold

        # Collect all photos with app attribution
        photo_records: list[dict[str, Any]] = []
        for app in applications:
            d_id = app["dossier_id"]
            inst = app.get("institution_name", d_id)
            for ent in app.get("entities", []):
                if ent.entity_type == EntityType.PHOTO_PHASH:
                    photo_records.append({
                        "dossier_id": d_id,
                        "institution_name": inst,
                        "phash": ent.entity_value,
                        "label": ent.label,
                        "metadata": ent.metadata or {},
                    })

        # Pairwise cross-application comparison
        for i, p1 in enumerate(photo_records):
            for p2 in photo_records[i + 1 :]:
                if p1["dossier_id"] == p2["dossier_id"]:
                    continue  # Intra-application comparison handled by forensics

                dist = hamming_distance(p1["phash"], p2["phash"])
                if dist <= max_dist:
                    involved_ids = sorted([p1["dossier_id"], p2["dossier_id"]])
                    evidence_list = [
                        EvidenceItem(
                            evidence_id=f"ev-photo-{p1['dossier_id']}-{p1['phash'][:8]}",
                            trust_level=TrustLevel.STRUCTURAL_FORENSIC,
                            source_type="Campus / Lab Photograph",
                            description=(
                                f"Photo '{p1['label']}' (pHash: {p1['phash']}) submitted by "
                                f"{p1['institution_name']}"
                            ),
                            raw_value={"phash": p1["phash"], "hamming_distance": dist},
                            source_document_id=p1["dossier_id"],
                            source_document_name=p1["institution_name"],
                            verification_method="PERCEPTUAL_PHASH_HAMMING",
                            is_self_attested=False,
                            is_tampered=True,
                        ),
                        EvidenceItem(
                            evidence_id=f"ev-photo-{p2['dossier_id']}-{p2['phash'][:8]}",
                            trust_level=TrustLevel.STRUCTURAL_FORENSIC,
                            source_type="Campus / Lab Photograph",
                            description=(
                                f"Photo '{p2['label']}' (pHash: {p2['phash']}) submitted by "
                                f"{p2['institution_name']}"
                            ),
                            raw_value={"phash": p2["phash"], "hamming_distance": dist},
                            source_document_id=p2["dossier_id"],
                            source_document_name=p2["institution_name"],
                            verification_method="PERCEPTUAL_PHASH_HAMMING",
                            is_self_attested=False,
                            is_tampered=True,
                        ),
                    ]

                    match_type = "Identical" if dist == 0 else f"Near-identical (distance {dist})"
                    f = Finding(
                        finding_id=f"fnd-photo-{uuid.uuid4().hex[:8]}",
                        rule_id=cls.RULE_ID,
                        rule_name=cls.RULE_NAME,
                        category="Physical Asset Integrity",
                        status=VerificationStatus.FLAGGED_TAMPER,
                        summary=(
                            f"{match_type} photograph detected across separate applicants "
                            f"({p1['institution_name']} vs {p2['institution_name']})."
                        ),
                        details=(
                            f"Perceptual hash analysis revealed a visual match with Hamming distance {dist} "
                            f"(threshold: {max_dist}) between photos submitted by {p1['institution_name']} "
                            f"and {p2['institution_name']}. The AICTE Approval Process Handbook prohibits recycling "
                            f"laboratory, classroom, or infrastructure photographs across independent institutions."
                        ),
                        handbook_citation=HandbookCitation(
                            handbook="AICTE Approval Process Handbook 2024-2027",
                            clause="Clause 6.2",
                            page=82,
                            edition="2024-2027",
                        ),
                        evidence_list=evidence_list,
                        advisory_notes=[
                            f"Involved Application IDs: {', '.join(involved_ids)}",
                            f"pHash 1: {p1['phash']}, pHash 2: {p2['phash']}, Bit Distance: {dist}",
                            "Conduct physical surprise inspection with geo-tagged photographic audit.",
                        ],
                    )
                    findings.append(f)

        return findings


class SealReuseDetector:
    """Detects reuse of the same physical/digital seal across different issuing authorities."""

    RULE_ID = "AICTE-FRAUD-SEAL-REUSE"
    RULE_NAME = "Seal Reuse: Stamp Digital Clone Across Different Issuing Authorities"

    @classmethod
    def detect(
        cls,
        applications: list[dict[str, Any]],
        threshold: int | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        max_dist = threshold if threshold is not None else settings.fraud_seal_hamming_threshold

        seal_records: list[dict[str, Any]] = []
        for app in applications:
            d_id = app["dossier_id"]
            inst = app.get("institution_name", d_id)
            for ent in app.get("entities", []):
                if ent.entity_type == EntityType.SEAL_PHASH:
                    meta = ent.metadata or {}
                    auth = meta.get("issuing_authority", "Official Statutory Authority")
                    seal_records.append({
                        "dossier_id": d_id,
                        "institution_name": inst,
                        "phash": ent.entity_value,
                        "authority": auth,
                        "norm_authority": normalize_authority_name(auth),
                        "label": ent.label,
                        "metadata": meta,
                    })

        for i, s1 in enumerate(seal_records):
            for s2 in seal_records[i + 1 :]:
                # If normalized authorities are different, check if seals are perceptually identical/near-identical
                if s1["norm_authority"] and s2["norm_authority"] and s1["norm_authority"] != s2["norm_authority"]:
                    dist = hamming_distance(s1["phash"], s2["phash"])
                    if dist <= max_dist:
                        involved_ids = sorted({s1["dossier_id"], s2["dossier_id"]})
                        evidence_list = [
                            EvidenceItem(
                                evidence_id=f"ev-seal-{s1['dossier_id']}-{s1['phash'][:8]}",
                                trust_level=TrustLevel.STRUCTURAL_FORENSIC,
                                source_type="Official Stamp / Seal",
                                description=(
                                    f"Seal stamped by alleged authority '{s1['authority']}' "
                                    f"(pHash: {s1['phash']}) on application {s1['dossier_id']}"
                                ),
                                raw_value={"authority": s1["authority"], "phash": s1["phash"]},
                                source_document_id=s1["dossier_id"],
                                source_document_name=s1["institution_name"],
                                verification_method="SEAL_PHASH_CROSS_AUTHORITY",
                                is_self_attested=False,
                                is_tampered=True,
                            ),
                            EvidenceItem(
                                evidence_id=f"ev-seal-{s2['dossier_id']}-{s2['phash'][:8]}",
                                trust_level=TrustLevel.STRUCTURAL_FORENSIC,
                                source_type="Official Stamp / Seal",
                                description=(
                                    f"Seal stamped by alleged authority '{s2['authority']}' "
                                    f"(pHash: {s2['phash']}) on application {s2['dossier_id']}"
                                ),
                                raw_value={"authority": s2["authority"], "phash": s2["phash"]},
                                source_document_id=s2["dossier_id"],
                                source_document_name=s2["institution_name"],
                                verification_method="SEAL_PHASH_CROSS_AUTHORITY",
                                is_self_attested=False,
                                is_tampered=True,
                            ),
                        ]

                        f = Finding(
                            finding_id=f"fnd-seal-{uuid.uuid4().hex[:8]}",
                            rule_id=cls.RULE_ID,
                            rule_name=cls.RULE_NAME,
                            category="Forensic Document Integrity",
                            status=VerificationStatus.FLAGGED_TAMPER,
                            summary=(
                                f"Digital Seal Clone Across Different Authorities: '{s1['authority']}' "
                                f"vs '{s2['authority']}' (distance: {dist})."
                            ),
                            details=(
                                f"A statutory seal image with perceptual hash {s1['phash']} was claimed by "
                                f"'{s1['authority']}' in {s1['institution_name']}, but the near-identical seal "
                                f"(pHash {s2['phash']}, distance {dist}) was also used under alleged authority "
                                f"'{s2['authority']}' in {s2['institution_name']}. An authentic physical stamp "
                                f"cannot legitimately exist across disparate municipal or governmental authorities, "
                                f"indicating digital cloning or forged template reuse."
                            ),
                            handbook_citation=HandbookCitation(
                                handbook="AICTE Approval Process Handbook 2024-2027",
                                clause="Clause 1.4 & Appendix 1",
                                page=22,
                                edition="2024-2027",
                            ),
                            evidence_list=evidence_list,
                            advisory_notes=[
                                f"Involved Application IDs: {', '.join(involved_ids)}",
                                f"Authority A: {s1['authority']}, Authority B: {s2['authority']}, Distance: {dist}",
                                "Notify forensic vigilance and issue show-cause inquiry.",
                            ],
                        )
                        findings.append(f)

        return findings


class FraudDetectorEngine:
    """Orchestrates all cross-application fraud detectors."""

    @classmethod
    def run_all(
        cls,
        applications: list[dict[str, Any]],
        photo_threshold: int | None = None,
        seal_threshold: int | None = None,
    ) -> list[Finding]:
        """Execute Ghost Faculty, Certificate Sharing, Photo Reuse, and Seal Reuse detectors."""
        findings: list[Finding] = []
        findings.extend(GhostFacultyDetector.detect(applications))
        findings.extend(CertificateSharingDetector.detect(applications))
        findings.extend(PhotoReuseDetector.detect(applications, threshold=photo_threshold))
        findings.extend(SealReuseDetector.detect(applications, threshold=seal_threshold))

        # Enforce trust constraints on all findings
        for f in findings:
            f.validate_trust_integrity()

        return findings
