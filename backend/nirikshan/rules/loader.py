"""Ruleset loader with SHA-256 integrity hash and year filtering.

Responsibilities:
- Load YAML rulesets from the rulesets directory
- Compute SHA-256 of the raw YAML bytes for tamper-evident auditing
- Validate all rules against the Rule Pydantic schema
- Filter rules by academic year
- Cache parsed rulesets to avoid redundant I/O
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from nirikshan.config import settings
from nirikshan.core.rule_schema import Rule, RulesetMeta


class RulesetLoadError(Exception):
    """Raised when a ruleset YAML fails to load or validate."""


def _compute_sha256(raw_bytes: bytes) -> str:
    return hashlib.sha256(raw_bytes).hexdigest()


def _coerce_rule_dict(raw: dict[str, Any]) -> dict[str, Any]:
    """Coerce legacy/shorthand YAML fields to the canonical Rule schema shape.

    The sample YAML uses slightly different field names in some places
    (e.g. ``id`` → ``rule_id``, ``name`` → ``title``).  This function
    bridges the gap without changing the YAML files.
    """
    r = dict(raw)

    # id → rule_id
    if "rule_id" not in r and "id" in r:
        r["rule_id"] = r.pop("id")

    # name → title
    if "title" not in r and "name" in r:
        r["title"] = r.pop("name")

    # citation: merge legacy flat fields into nested RuleCitation shape
    if "citation" not in r:
        cit: dict[str, Any] = {}
        for key in ("document", "clause", "page", "edition", "table", "needs_verification"):
            if key in r:
                cit[key] = r.pop(key)
        # Try legacy handbook key
        if "handbook" in r:
            cit["document"] = r.pop("handbook")
        # Fallback: build from known ruleset keys
        if "document" not in cit:
            cit["document"] = "AICTE Approval Process Handbook (sample)"
        if "clause" not in cit:
            cit["clause"] = "N/A"
        if "page" not in cit:
            cit["page"] = "TODO"
        r["citation"] = cit
    else:
        # Ensure nested citation has document field
        cit = dict(r["citation"])
        if "document" not in cit and "handbook" in cit:
            cit["document"] = cit.pop("handbook")
        if "document" not in cit:
            cit["document"] = "AICTE Approval Process Handbook (sample)"
        r["citation"] = cit

    # applicable_years: default if missing
    if "applicable_years" not in r:
        r["applicable_years"] = ["2024-2025", "2025-2026", "2026-2027"]

    # evidence_requirements: build from required_document_types if missing
    if "evidence_requirements" not in r:
        req_types: list[str] = r.pop("required_document_types", [])
        r["evidence_requirements"] = [
            {"type": t, "min_trust_level": "RECORD"} for t in req_types
        ]
    else:
        # Drop redundant key if both exist
        r.pop("required_document_types", None)

    # severity normalisation
    sev_map = {
        "CRITICAL": "CRITICAL",
        "HIGH": "HIGH",
        "MEDIUM": "MEDIUM",
        "LOW": "LOW",
        "INFO": "INFO",
    }
    r["severity"] = sev_map.get(str(r.get("severity", "MEDIUM")).upper(), "MEDIUM")

    # needs_verification: escalate from citation if present there
    if r["citation"].get("needs_verification"):
        r["needs_verification"] = True
    else:
        r.setdefault("needs_verification", False)

    # Remove unknown keys that Pydantic strict mode would reject
    known_keys = {
        "rule_id", "title", "citation", "applicable_years", "category",
        "evidence_requirements", "logic", "severity", "deficiency_template",
        "needs_verification", "description", "tags", "parameters",
    }
    for unknown in list(r.keys()):
        if unknown not in known_keys:
            r.pop(unknown)

    return r


class RulesetLoader:
    """Loads, validates, hashes, and caches YAML rulesets."""

    def __init__(self, rules_dir: Path | None = None) -> None:
        self._rules_dir = rules_dir or settings.rulesets_dir
        self._cache: dict[str, RulesetMeta] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, filename: str) -> RulesetMeta:
        """Load and validate a ruleset YAML file, returning a RulesetMeta.

        Results are cached by filename key.  The SHA-256 of the raw bytes
        is stored in RulesetMeta.sha256_hash.
        """
        if filename in self._cache:
            return self._cache[filename]

        file_path = self._rules_dir / filename
        if not file_path.exists():
            raise RulesetLoadError(f"Ruleset file not found: {file_path}")

        raw_bytes = file_path.read_bytes()
        sha256 = _compute_sha256(raw_bytes)

        try:
            data: dict[str, Any] = yaml.safe_load(raw_bytes.decode("utf-8"))
        except yaml.YAMLError as exc:
            raise RulesetLoadError(f"YAML parse error in {filename}: {exc}") from exc

        if not isinstance(data, dict):
            raise RulesetLoadError(f"Ruleset {filename} must be a YAML mapping at top level")

        raw_rules: list[dict[str, Any]] = data.get("rules", [])
        validated_rules: list[Rule] = []
        errors: list[str] = []

        for i, raw_rule in enumerate(raw_rules):
            coerced = _coerce_rule_dict(dict(raw_rule))
            try:
                validated_rules.append(Rule.model_validate(coerced))
            except ValidationError as exc:
                rule_id = raw_rule.get("rule_id") or raw_rule.get("id") or f"[index {i}]"
                errors.append(f"Rule {rule_id}: {exc}")

        if errors:
            raise RulesetLoadError(
                f"Validation errors in {filename}:\n" + "\n".join(errors)
            )

        meta = RulesetMeta(
            version=str(data.get("version", "unknown")),
            handbook_title=str(data.get("handbook_title", filename)),
            publisher=data.get("publisher"),
            effective_from=data.get("effective_from"),
            sha256_hash=sha256,
            rules=validated_rules,
        )
        self._cache[filename] = meta
        return meta

    def filter_by_year(self, filename: str, academic_year: str) -> list[Rule]:
        """Return rules from *filename* that apply to *academic_year*."""
        meta = self.load(filename)
        return meta.filter_by_year(academic_year)

    def list_available(self) -> list[str]:
        """Return all *.yaml filenames in the rulesets directory."""
        return [p.name for p in self._rules_dir.glob("*.yaml")]

    def invalidate_cache(self, filename: str | None = None) -> None:
        """Clear cached ruleset(s)."""
        if filename:
            self._cache.pop(filename, None)
        else:
            self._cache.clear()


# Module-level singleton
ruleset_loader = RulesetLoader()
