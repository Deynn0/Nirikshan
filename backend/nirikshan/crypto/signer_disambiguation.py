"""Signer disambiguation module for institutional and regulatory scrutiny.

Classifies certificate signers as:
- ISSUER_OFFICER: An authorized signatory from a verified municipal, state, or central regulatory body.
- APPLICANT: The applying institution, trust, society, or authorized applicant signatory.
- UNKNOWN: An unverified third party or unmapped organization.

Non-negotiable rule:
An applicant-signed document must never reach Cryptographic-level trust as issuer proof.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

import yaml
from rapidfuzz import fuzz

from nirikshan.config import settings
from nirikshan.trust.ladder import TrustLevel


class SignerRole(StrEnum):
    """Signer classification role."""

    ISSUER_OFFICER = "ISSUER_OFFICER"
    APPLICANT = "APPLICANT"
    UNKNOWN = "UNKNOWN"


@dataclass
class ApplicantIdentity:
    """Declared identity of the applicant institution for scrutiny comparison."""

    institution_name: str | None = None
    applicant_name: str | None = None
    email: str | None = None
    trust_or_society_name: str | None = None
    application_number: str | None = None


@dataclass
class IssuerEntry:
    """Registered issuing authority."""

    id: str
    name: str
    category: str = "REGULATORY_COUNCIL"
    org_patterns: list[str] = field(default_factory=list)
    ou_patterns: list[str] = field(default_factory=list)
    cn_patterns: list[str] = field(default_factory=list)
    trusted_roles: list[str] = field(default_factory=lambda: ["ISSUER_OFFICER"])


class IssuerRegistry:
    """Loads and matches certificates against known governmental/municipal issuers."""

    def __init__(self, registry_path: Path | None = None) -> None:
        self.registry_path = registry_path or settings.issuers_yaml_path
        self.issuers: list[IssuerEntry] = []
        self._load()

    def _load(self) -> None:
        if not self.registry_path.exists():
            return
        try:
            with open(self.registry_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            raw_issuers = data.get("issuers", [])
            self.issuers = [
                IssuerEntry(
                    id=item.get("id", ""),
                    name=item.get("name", ""),
                    category=item.get("category", "REGULATORY_COUNCIL"),
                    org_patterns=item.get("org_patterns", []),
                    ou_patterns=item.get("ou_patterns", []),
                    cn_patterns=item.get("cn_patterns", []),
                    trusted_roles=item.get("trusted_roles", ["ISSUER_OFFICER"]),
                )
                for item in raw_issuers
            ]
        except Exception:
            # Fallback to empty registry on read error
            self.issuers = []

    def match_issuer(self, subject: dict[str, str]) -> IssuerEntry | None:
        """Match certificate subject fields against issuer patterns."""
        cn = (subject.get("common_name") or subject.get("CN") or "").strip()
        org = (subject.get("organization_name") or subject.get("O") or "").strip()
        ou = (subject.get("organizational_unit_name") or subject.get("OU") or "").strip()

        for issuer in self.issuers:
            # Check organization match
            for pat in issuer.org_patterns:
                if org and fnmatch.fnmatch(org.lower(), pat.lower()):
                    return issuer
                if cn and fnmatch.fnmatch(cn.lower(), pat.lower()):
                    return issuer

            # Check OU match
            for pat in issuer.ou_patterns:
                if ou and fnmatch.fnmatch(ou.lower(), pat.lower()):
                    return issuer

            # Check CN match
            for pat in issuer.cn_patterns:
                if cn and fnmatch.fnmatch(cn.lower(), pat.lower()):
                    return issuer

        return None


@dataclass
class SignerDisambiguationResult:
    """Result of disambiguating a digital signature."""

    role: SignerRole
    matched_issuer: IssuerEntry | None = None
    reason: str = ""
    is_applicant_match: bool = False
    effective_trust_level: TrustLevel = TrustLevel.STRUCTURAL_FORENSIC


def _normalize(text: str | None) -> str:
    if not text:
        return ""
    return "".join(ch.lower() for ch in text if ch.isalnum() or ch.isspace()).strip()


def matches_applicant(
    subject: dict[str, str],
    applicant: ApplicantIdentity,
) -> tuple[bool, str]:
    """Determine whether the certificate subject belongs to the applicant."""
    cn = subject.get("common_name") or subject.get("CN") or ""
    org = subject.get("organization_name") or subject.get("O") or ""
    email = subject.get("email_address") or subject.get("email") or ""

    norm_cn = _normalize(cn)
    norm_org = _normalize(org)
    norm_email = (email or "").strip().lower()

    # Compare against institution name
    if applicant.institution_name:
        inst_norm = _normalize(applicant.institution_name)
        if inst_norm:
            if inst_norm in norm_org or inst_norm in norm_cn:
                return True, f"Subject matches institution name '{applicant.institution_name}'"
            if norm_org and fuzz.token_set_ratio(inst_norm, norm_org) >= 85:
                return True, f"Subject organization closely matches institution name '{applicant.institution_name}'"
            if norm_cn and fuzz.token_set_ratio(inst_norm, norm_cn) >= 85:
                return True, f"Subject CN closely matches institution name '{applicant.institution_name}'"

    # Compare against applicant person name
    if applicant.applicant_name:
        app_norm = _normalize(applicant.applicant_name)
        if app_norm and (app_norm in norm_cn or fuzz.token_set_ratio(app_norm, norm_cn) >= 90):
            return True, f"Signer CN matches applicant name '{applicant.applicant_name}'"

    # Compare against Trust or Society name
    if applicant.trust_or_society_name:
        trust_norm = _normalize(applicant.trust_or_society_name)
        if trust_norm:
            if trust_norm in norm_org or trust_norm in norm_cn:
                return True, f"Subject matches applicant sponsoring trust/society '{applicant.trust_or_society_name}'"
            if norm_org and fuzz.token_set_ratio(trust_norm, norm_org) >= 85:
                return True, f"Subject organization matches trust '{applicant.trust_or_society_name}'"

    # Compare email
    if applicant.email and norm_email and applicant.email.strip().lower() == norm_email:
        return True, f"Signer email matches applicant declared email '{applicant.email}'"

    return False, ""


def disambiguate_signer(
    subject: dict[str, str],
    applicant: ApplicantIdentity | None = None,
    registry: IssuerRegistry | None = None,
    *,
    is_valid_sig: bool = True,
    is_trusted_chain: bool = False,
    is_tampered: bool = False,
    document_role_required: str | None = None,  # e.g. "ISSUER"
) -> SignerDisambiguationResult:
    """Disambiguate signer role and assign appropriate Trust Ladder level.

    Guarantees:
    - Tampered document -> STRUCTURAL_FORENSIC.
    - Applicant-signed document -> UNVERIFIED_CLAIM as issuer proof (never CRYPTOGRAPHIC).
    - Verified Issuer Officer with trusted chain -> CRYPTOGRAPHIC.
    - Verified Issuer Officer with self-signed / local anchor -> ISSUER.
    """
    if is_tampered:
        return SignerDisambiguationResult(
            role=SignerRole.UNKNOWN,
            reason="Document integrity verification failed (tampered).",
            effective_trust_level=TrustLevel.STRUCTURAL_FORENSIC,
        )

    # 1. First test if signer is the applicant
    if applicant:
        is_app, app_reason = matches_applicant(subject, applicant)
        if is_app:
            return SignerDisambiguationResult(
                role=SignerRole.APPLICANT,
                reason=f"Signer classified as APPLICANT: {app_reason}. Self-attestation cannot provide issuer cryptographic proof.",
                is_applicant_match=True,
                effective_trust_level=TrustLevel.UNVERIFIED_CLAIM,
            )

    # 2. Check against Issuer Registry
    issuer_reg = registry or IssuerRegistry()
    matched = issuer_reg.match_issuer(subject)

    if matched:
        # Signer is recognized as an authorized regulatory / municipal issuer officer
        if is_valid_sig and is_trusted_chain:
            trust = TrustLevel.CRYPTOGRAPHIC
            reason = f"Verified ISSUER_OFFICER from {matched.name} with trusted PKI chain."
        elif is_valid_sig:
            trust = TrustLevel.ISSUER
            reason = f"Verified ISSUER_OFFICER from {matched.name} (cryptographically intact, untrusted local root)."
        else:
            trust = TrustLevel.STRUCTURAL_FORENSIC
            reason = f"Issuer officer claimed ({matched.name}), but digital signature is invalid."

        return SignerDisambiguationResult(
            role=SignerRole.ISSUER_OFFICER,
            matched_issuer=matched,
            reason=reason,
            is_applicant_match=False,
            effective_trust_level=trust,
        )

    # 3. Unrecognized signer
    org = subject.get("organization_name") or subject.get("O") or "Unknown Org"
    cn = subject.get("common_name") or subject.get("CN") or "Unknown Signer"
    return SignerDisambiguationResult(
        role=SignerRole.UNKNOWN,
        reason=f"Signer '{cn}' ({org}) does not match registered issuing authorities or declared applicant.",
        is_applicant_match=False,
        effective_trust_level=TrustLevel.STRUCTURAL_FORENSIC if is_valid_sig else TrustLevel.UNVERIFIED_CLAIM,
    )
