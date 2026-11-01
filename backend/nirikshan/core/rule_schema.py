"""Pydantic Rule schema for AICTE regulatory rules (Phase 1).

All fields as specified in the Phase 1 deliverables:
- rule_id, title, citation, applicable_years, category,
  evidence_requirements, logic, severity, deficiency_template,
  needs_verification.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Sub-schemas
# ---------------------------------------------------------------------------


class RuleCitation(BaseModel):
    """Source citation for a regulatory rule."""

    document: str = Field(..., description="Full handbook / gazette title")
    clause: str = Field(..., description="Clause or section reference, e.g. 'Clause 4.1'")
    page: int | str = Field(..., description="Page number or 'TODO' if unverified")
    edition: str | None = None
    table: str | None = None
    needs_verification: bool = Field(
        default=False,
        description="True when citation is a placeholder or unconfirmed draft",
    )


class EvidenceRequirement(BaseModel):
    """Evidence type and minimum acceptable trust level for a rule."""

    type: str = Field(..., description="Document / evidence type, e.g. 'FIRE_SAFETY_NOC'")
    min_trust_level: str = Field(
        ...,
        description=(
            "Minimum TrustLevel required. One of: CRYPTOGRAPHIC, ISSUER, RECORD, "
            "RULE, STRUCTURAL_FORENSIC, MODEL, UNVERIFIED_CLAIM"
        ),
    )

    @field_validator("min_trust_level")
    @classmethod
    def validate_trust_level(cls, v: str) -> str:
        allowed = {
            "CRYPTOGRAPHIC",
            "ISSUER",
            "RECORD",
            "RULE",
            "STRUCTURAL_FORENSIC",
            "MODEL",
            "UNVERIFIED_CLAIM",
        }
        if v not in allowed:
            raise ValueError(f"min_trust_level must be one of {allowed}, got {v!r}")
        return v


class RuleSeverity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


# ---------------------------------------------------------------------------
# Primary Rule schema
# ---------------------------------------------------------------------------


class Rule(BaseModel):
    """Atomic declarative regulatory rule.

    Fields are directly derived from the Phase 1 specification.
    """

    rule_id: str = Field(
        ...,
        pattern=r"^[A-Z0-9][A-Z0-9\-_]{2,63}$",
        description="Unique deterministic rule identifier, e.g. 'AICTE-FIRE-NOC-001'",
    )
    title: str = Field(..., min_length=3, description="Human-readable rule title")

    citation: RuleCitation = Field(..., description="Regulatory source citation")

    applicable_years: list[str] = Field(
        ...,
        min_length=1,
        description="Academic years this rule applies to, e.g. ['2024-2025', '2025-2026']",
    )

    category: str = Field(
        ...,
        description="Regulatory domain category, e.g. 'Safety & Compliance'",
    )

    evidence_requirements: list[EvidenceRequirement] = Field(
        default_factory=list,
        description="What evidence types are required and at what minimum trust level",
    )

    logic: str | None = Field(
        default=None,
        description=(
            "Declarative pass/fail expression evaluated by the safe AST evaluator. "
            "Supports: comparisons (<, <=, >, >=, ==, !=), boolean ops (and, or, not), "
            "set membership (in), date arithmetic. "
            "Example: 'land_area_acres >= required_area and is_contiguous == True'"
        ),
    )

    severity: RuleSeverity = RuleSeverity.MEDIUM

    deficiency_template: str | None = Field(
        default=None,
        description=(
            "Jinja2-style template for the deficiency message rendered on FAIL. "
            "Variables wrapped in {braces} are substituted from the facts dict. "
            "Example: 'Requires {required_area} acres; only {land_area_acres} provided.'"
        ),
    )

    needs_verification: bool = Field(
        default=False,
        description="True when the rule itself (or its citation) requires expert review",
    )

    # Optional metadata
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Static parameters referenced in logic expressions",
    )

    @model_validator(mode="after")
    def sync_needs_verification(self) -> Rule:
        """If citation.needs_verification is True, escalate to rule level."""
        if self.citation.needs_verification:
            self.needs_verification = True
        return self

    @property
    def display_citation(self) -> str:
        """Short human-readable citation string."""
        parts = [self.citation.document, self.citation.clause]
        if self.citation.table:
            parts.append(self.citation.table)
        if isinstance(self.citation.page, int):
            parts.append(f"p.{self.citation.page}")
        else:
            parts.append(f"p.{self.citation.page}")
        return " | ".join(parts)


# ---------------------------------------------------------------------------
# Ruleset envelope (wraps a collection of rules loaded from YAML)
# ---------------------------------------------------------------------------


class RulesetMeta(BaseModel):
    """Metadata envelope for a loaded ruleset file."""

    version: str
    handbook_title: str
    publisher: str | None = None
    effective_from: str | None = None
    sha256_hash: str = Field(default="", description="SHA-256 of the raw YAML bytes")
    rules: list[Rule] = Field(default_factory=list)

    def filter_by_year(self, academic_year: str) -> list[Rule]:
        """Return only rules applicable to the given academic_year string."""
        return [r for r in self.rules if academic_year in r.applicable_years]
