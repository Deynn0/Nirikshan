"""Entity extraction pipeline for cross-application fraud detection.

Extracts and normalizes institutional entities per application:
1. Faculty IDs (Aadhaar/PAN converted strictly to salted HMAC-SHA256 hashes).
2. Certificate numbers (Fire NOC, Building Completion, etc.).
3. File SHA-256 cryptographic hashes.
4. Photo perceptual hashes (pHash for lab and campus photos).
5. Seal perceptual hashes with issuing authority attribution.
6. Land registration numbers (Sub-Registrar deeds, khasra/survey numbers).
7. Declared campus and institutional addresses.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from nirikshan.fraud.hasher import hash_salted_identity, mask_identity_label
from nirikshan.fraud.models import (
    ApplicationEntityEdge,
    EntityExtractionResult,
    EntityType,
    ExtractedEntity,
)

logger = logging.getLogger(__name__)


def normalize_string_key(val: str) -> str:
    """Normalize strings for deterministic entity keys."""
    if not val:
        return ""
    # Strip non-alphanumeric, collapse spaces, uppercase
    cleaned = re.sub(r"[^\w\s\-\/]", "", str(val).strip())
    return re.sub(r"\s+", " ", cleaned).strip().upper()


def normalize_address(addr: str) -> str:
    """Normalize address for matching across dossiers."""
    if not addr:
        return ""
    lower = addr.strip().lower()
    # Remove common punctuation
    clean = re.sub(r"[\.,\-#\/]", " ", lower)
    # Collapse whitespace
    tokens = clean.split()
    return " ".join(tokens)


class EntityExtractor:
    """Extracts regulatory entities from application dossiers and documents."""

    def __init__(self, salt: str | None = None) -> None:
        self.salt = salt

    def extract_from_dossier_data(
        self,
        dossier_id: str,
        application_number: str,
        institution_name: str,
        documents: list[dict[str, Any]] | list[Any] | None = None,
        extracted_params: dict[str, Any] | None = None,
        extra_entities: list[ExtractedEntity] | None = None,
    ) -> EntityExtractionResult:
        """Extract all compliance entities for a given application dossier."""
        params = extracted_params or {}
        docs = documents or []

        entities: list[ExtractedEntity] = []
        edges: list[ApplicationEntityEdge] = []
        seen_entity_ids: set[str] = set()

        def _add_entity(ent: ExtractedEntity, context_label: str = "") -> None:
            if ent.entity_id not in seen_entity_ids:
                seen_entity_ids.add(ent.entity_id)
                entities.append(ent)
                edges.append(
                    ApplicationEntityEdge(
                        edge_id=f"edge:{dossier_id}:{ent.entity_id}",
                        dossier_id=dossier_id,
                        entity_id=ent.entity_id,
                        relation="uses",
                        context_label=context_label or ent.label,
                        metadata={"institution_name": institution_name, **ent.metadata},
                    )
                )

        # 1. Faculty IDs (Aadhaar / PAN -> Salted Hashes)
        faculty_items = params.get("faculty_list") or params.get("faculty") or []
        for fac in faculty_items:
            raw_id = (
                fac.get("aadhaar")
                or fac.get("pan")
                or fac.get("id_number")
                or fac.get("identity_number")
            )
            salted_hash = fac.get("id_salted_hash") or fac.get("faculty_hash")

            if raw_id:
                # Salted hash calculation - PLAINTEXT NEVER STORED
                salted_hash = hash_salted_identity(raw_id, salt=self.salt)
                display_label = f"Faculty ({mask_identity_label(raw_id)})"
            elif salted_hash:
                display_label = f"Faculty (Hash: {salted_hash[:8]}...)"
            else:
                continue

            emp_type = str(fac.get("employment_type", "FULL_TIME")).upper()
            periods = fac.get("periods") or fac.get("academic_years") or []
            if not periods and ("start_year" in fac or "end_year" in fac):
                periods = [f"{fac.get('start_year', '')}-{fac.get('end_year', '')}"]
            if not periods and "academic_year" in fac:
                periods = [str(fac["academic_year"])]
            if not periods:
                periods = ["2024-2025"]  # Default active inspection session

            ent = ExtractedEntity(
                entity_id=f"FACULTY:{salted_hash}",
                entity_type=EntityType.FACULTY,
                entity_value=salted_hash,
                label=display_label,
                metadata={
                    "faculty_name": fac.get("name", "Unknown Faculty"),
                    "employment_type": emp_type,
                    "periods": periods,
                    "department": fac.get("department", "Engineering"),
                    "designation": fac.get("designation", "Assistant Professor"),
                    "institution_name": institution_name,
                },
            )
            _add_entity(ent, context_label=f"{emp_type} Faculty: {ent.label}")

        # 2. Certificate Numbers (Fire NOC, Building Completion, etc.)
        cert_items = params.get("certificates") or []
        if isinstance(cert_items, list):
            for c in cert_items:
                c_num = c.get("number") or c.get("certificate_number")
                c_type = c.get("type", "GENERAL_NOC")
                if c_num:
                    norm_num = normalize_string_key(c_num)
                    ent = ExtractedEntity(
                        entity_id=f"CERTIFICATE:{norm_num}",
                        entity_type=EntityType.CERTIFICATE,
                        entity_value=norm_num,
                        label=f"Cert: {c_type} #{norm_num}",
                        metadata={
                            "cert_type": c_type,
                            "raw_number": c_num,
                            "issuing_authority": c.get("issuing_authority", "Statutory Authority"),
                            "issue_date": str(c.get("issue_date", "")),
                            "valid_upto": str(c.get("valid_upto", "")),
                            "institution_name": institution_name,
                        },
                    )
                    _add_entity(ent, context_label=f"{c_type} #{norm_num}")

        # Direct certificate parameters in params
        if "fire_noc_number" in params and params["fire_noc_number"]:
            f_num = normalize_string_key(params["fire_noc_number"])
            ent = ExtractedEntity(
                entity_id=f"CERTIFICATE:{f_num}",
                entity_type=EntityType.CERTIFICATE,
                entity_value=f_num,
                label=f"Fire NOC #{f_num}",
                metadata={
                    "cert_type": "FIRE_SAFETY_NOC",
                    "raw_number": params["fire_noc_number"],
                    "issuing_authority": params.get("fire_noc_authority", "Fire & Emergency Services"),
                    "institution_name": institution_name,
                },
            )
            _add_entity(ent, context_label=f"Fire NOC #{f_num}")

        # 3. File SHA-256 Hashes
        for d in docs:
            sha = None
            f_name = "Document"
            doc_type = "UNKNOWN"
            if isinstance(d, dict):
                sha = d.get("sha256_hash") or d.get("sha256")
                f_name = d.get("file_name", "Document")
                doc_type = d.get("doc_type", "UNKNOWN")
            elif hasattr(d, "sha256_hash"):
                sha = d.sha256_hash
                f_name = getattr(d, "file_name", "Document")
                doc_type = getattr(d, "doc_type", "UNKNOWN")

            if sha:
                sha_norm = str(sha).strip().lower()
                ent = ExtractedEntity(
                    entity_id=f"FILE_HASH:{sha_norm}",
                    entity_type=EntityType.FILE_HASH,
                    entity_value=sha_norm,
                    label=f"File: {f_name} ({sha_norm[:8]}...)",
                    metadata={
                        "file_name": f_name,
                        "doc_type": str(doc_type),
                        "institution_name": institution_name,
                    },
                )
                _add_entity(ent, context_label=f"Doc SHA-256: {f_name}")

        # 4. Photo Perceptual Hashes (Lab and Campus Photos)
        photo_items = params.get("photos") or params.get("lab_photos") or []
        for p in photo_items:
            phash = p.get("phash") or p.get("perceptual_hash")
            if phash:
                phash_norm = str(phash).strip().lower()
                p_type = p.get("type", "LAB_PHOTO")
                caption = p.get("description", p_type)
                ent = ExtractedEntity(
                    entity_id=f"PHOTO_PHASH:{phash_norm}",
                    entity_type=EntityType.PHOTO_PHASH,
                    entity_value=phash_norm,
                    label=f"Photo [{p_type}]: {caption} ({phash_norm[:8]})",
                    metadata={
                        "photo_type": p_type,
                        "description": caption,
                        "phash": phash_norm,
                        "institution_name": institution_name,
                    },
                )
                _add_entity(ent, context_label=f"Photo: {p_type}")

        # 5. Seal Perceptual Hashes (with Issuing Authority attribution)
        seal_items = params.get("seals") or []
        for s in seal_items:
            phash = s.get("phash") or s.get("perceptual_hash")
            authority = s.get("issuing_authority") or s.get("authority", "Official Authority")
            if phash:
                phash_norm = str(phash).strip().lower()
                ent = ExtractedEntity(
                    entity_id=f"SEAL_PHASH:{phash_norm}",
                    entity_type=EntityType.SEAL_PHASH,
                    entity_value=phash_norm,
                    label=f"Seal [{authority}]: {phash_norm[:8]}",
                    metadata={
                        "issuing_authority": authority,
                        "phash": phash_norm,
                        "doc_type": s.get("doc_type", "CERTIFICATE"),
                        "institution_name": institution_name,
                    },
                )
                _add_entity(ent, context_label=f"Seal: {authority}")

        # Also inspect document forensics if present for seals
        for d in docs:
            f_json: dict[str, Any] = {}
            if isinstance(d, dict):
                f_json = d.get("forensic_json") or d.get("forensic") or {}
                if isinstance(f_json, str):
                    try:
                        f_json = json.loads(f_json)
                    except Exception:
                        f_json = {}
            elif hasattr(d, "forensic_json"):
                raw = getattr(d, "forensic_json", "{}")
                if isinstance(raw, str):
                    try:
                        f_json = json.loads(raw)
                    except Exception:
                        f_json = {}

            if isinstance(f_json, dict) and "seals" in f_json:
                for s in f_json["seals"]:
                    ph = s.get("phash")
                    if ph:
                        ph_norm = str(ph).strip().lower()
                        auth = s.get("issuing_authority", "Sub-Registrar / Municipal Body")
                        ent = ExtractedEntity(
                            entity_id=f"SEAL_PHASH:{ph_norm}",
                            entity_type=EntityType.SEAL_PHASH,
                            entity_value=ph_norm,
                            label=f"Seal [{auth}]: {ph_norm[:8]}",
                            metadata={
                                "issuing_authority": auth,
                                "phash": ph_norm,
                                "institution_name": institution_name,
                            },
                        )
                        _add_entity(ent, context_label=f"Detected Seal: {auth}")

        # 6. Land Registration Numbers
        land_items = params.get("land_registrations") or []
        if isinstance(land_items, list):
            for l_item in land_items:
                reg_num = l_item.get("registration_number") or l_item.get("deed_number")
                if reg_num:
                    norm_reg = normalize_string_key(reg_num)
                    ent = ExtractedEntity(
                        entity_id=f"LAND_REG:{norm_reg}",
                        entity_type=EntityType.LAND_REG,
                        entity_value=norm_reg,
                        label=f"Land Deed #{norm_reg}",
                        metadata={
                            "raw_number": reg_num,
                            "sro_office": l_item.get("sro_office", ""),
                            "survey_numbers": l_item.get("survey_numbers", []),
                            "institution_name": institution_name,
                        },
                    )
                    _add_entity(ent, context_label=f"Land Deed #{norm_reg}")

        if "land_registration_number" in params and params["land_registration_number"]:
            l_num = normalize_string_key(params["land_registration_number"])
            ent = ExtractedEntity(
                entity_id=f"LAND_REG:{l_num}",
                entity_type=EntityType.LAND_REG,
                entity_value=l_num,
                label=f"Land Deed #{l_num}",
                metadata={
                    "raw_number": params["land_registration_number"],
                    "sro_office": params.get("sro_office", ""),
                    "institution_name": institution_name,
                },
            )
            _add_entity(ent, context_label=f"Land Deed #{l_num}")

        # 7. Declared Addresses
        declared_addr = (
            params.get("declared_address")
            or params.get("campus_address")
            or params.get("address")
        )
        if declared_addr:
            norm_addr = normalize_address(declared_addr)
            if len(norm_addr) > 5:
                # Key based on first 60 chars of normalized address to handle minor punctuation
                addr_slug = norm_addr[:60].replace(" ", "_")
                ent = ExtractedEntity(
                    entity_id=f"DECLARED_ADDRESS:{addr_slug}",
                    entity_type=EntityType.DECLARED_ADDRESS,
                    entity_value=norm_addr,
                    label=f"Address: {declared_addr[:40]}...",
                    metadata={
                        "raw_address": declared_addr,
                        "normalized_address": norm_addr,
                        "institution_name": institution_name,
                    },
                )
                _add_entity(ent, context_label="Declared Campus Address")

        # Add any explicitly supplied entities
        if extra_entities:
            for extra in extra_entities:
                _add_entity(extra, context_label=extra.label)

        return EntityExtractionResult(
            dossier_id=dossier_id,
            application_number=application_number,
            institution_name=institution_name,
            entities=entities,
            edges=edges,
        )
