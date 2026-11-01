"""Trust-gated rule runner: evaluates Rule.logic against facts.

Non-negotiable trust gating:
  - If the best evidence for a required evidence type is below the rule's
    min_trust_level, the result is UNVERIFIED (never PASS).
  - PASS is only emitted when all evidence requirements are met at or above
    their min_trust_level AND the logic expression evaluates True.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from nirikshan.core.rule_schema import Rule
from nirikshan.core.safe_eval import SafeEvalError, safe_evaluator
from nirikshan.trust.ladder import TRUST_RANKS, EvidenceItem, TrustLevel

# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


class RuleResultStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNVERIFIED = "UNVERIFIED"  # trust gate blocked PASS
    SKIP = "SKIP"  # rule not applicable (e.g. wrong year)
    ERROR = "ERROR"  # evaluator / config error


@dataclass
class EvidenceSummary:
    """Best evidence available for a single evidence requirement."""

    required_type: str
    min_trust_level: TrustLevel
    best_trust_level: TrustLevel | None
    is_satisfied: bool
    items: list[EvidenceItem] = field(default_factory=list)


@dataclass
class RuleResult:
    """Full result of evaluating a single Rule."""

    rule_id: str
    title: str
    status: RuleResultStatus
    logic_result: bool | None  # None if not evaluated
    message: str
    deficiency: str | None  # rendered deficiency_template on FAIL
    citation: str  # display citation
    needs_verification: bool
    evidence_summaries: list[EvidenceSummary] = field(default_factory=list)
    error: str | None = None


# ---------------------------------------------------------------------------
# Trust gate helper
# ---------------------------------------------------------------------------

TRUST_LEVEL_FROM_STR: dict[str, TrustLevel] = {t.value: t for t in TrustLevel}


def _best_trust_for_type(
    evidence_type: str,
    evidence_items: list[EvidenceItem],
) -> TrustLevel | None:
    """Find highest effective trust level among items matching evidence_type."""
    matching = [e for e in evidence_items if e.source_type == evidence_type]
    if not matching:
        return None
    best_rank = max(e.trust_rank for e in matching)
    # find the item with that rank
    for e in matching:
        if e.trust_rank == best_rank:
            return e.effective_trust_level()
    return None  # unreachable


def _check_trust_gate(
    rule: Rule,
    evidence_items: list[EvidenceItem],
) -> tuple[bool, list[EvidenceSummary]]:
    """Return (gate_passes, summaries).

    gate_passes is True only if every evidence requirement is satisfied
    at or above its min_trust_level.
    """
    summaries: list[EvidenceSummary] = []
    gate_passes = True

    for req in rule.evidence_requirements:
        req_level = TRUST_LEVEL_FROM_STR.get(req.min_trust_level, TrustLevel.RECORD)
        best_level = _best_trust_for_type(req.type, evidence_items)
        items_of_type = [e for e in evidence_items if e.source_type == req.type]

        is_advisory_or_claim = best_level in (TrustLevel.MODEL, TrustLevel.UNVERIFIED_CLAIM)
        satisfied = (
            best_level is not None
            and not is_advisory_or_claim
            and (TRUST_RANKS[best_level] >= TRUST_RANKS[req_level])
        )
        if not satisfied:
            gate_passes = False

        summaries.append(
            EvidenceSummary(
                required_type=req.type,
                min_trust_level=req_level,
                best_trust_level=best_level,
                is_satisfied=satisfied,
                items=items_of_type,
            )
        )

    return gate_passes, summaries


# ---------------------------------------------------------------------------
# Deficiency renderer
# ---------------------------------------------------------------------------


def _render_deficiency(template: str | None, facts: dict[str, Any]) -> str | None:
    """Render deficiency_template by substituting {key} placeholders from facts."""
    if not template:
        return None
    try:
        return template.format_map(facts)
    except (KeyError, ValueError):
        return template  # return un-rendered on error


# ---------------------------------------------------------------------------
# Core engine
# ---------------------------------------------------------------------------


class RuleEngine:
    """Evaluate a list of Rules against a facts dict and evidence items."""

    def evaluate_one(
        self,
        rule: Rule,
        facts: dict[str, Any],
        evidence_items: list[EvidenceItem] | None = None,
    ) -> RuleResult:
        """Evaluate a single rule.

        Steps:
        1. If logic is None → SKIP with note.
        2. Merge rule.parameters into a working facts namespace.
        3. Run trust gate: if any required evidence type is below min_trust_level
           → UNVERIFIED (never PASS).
        4. Evaluate logic expression via safe_evaluator.
        5. Render deficiency template if FAIL.
        """
        evidence_items = evidence_items or []

        # Merge static parameters into facts namespace (facts take priority)
        merged_facts: dict[str, Any] = {**rule.parameters, **facts}

        # Trust gate
        gate_passes, summaries = _check_trust_gate(rule, evidence_items)

        if rule.logic is None:
            return RuleResult(
                rule_id=rule.rule_id,
                title=rule.title,
                status=RuleResultStatus.SKIP,
                logic_result=None,
                message="No logic expression defined for this rule.",
                deficiency=None,
                citation=rule.display_citation,
                needs_verification=rule.needs_verification,
                evidence_summaries=summaries,
            )

        try:
            logic_result = bool(safe_evaluator.evaluate(rule.logic, merged_facts))
        except SafeEvalError as exc:
            return RuleResult(
                rule_id=rule.rule_id,
                title=rule.title,
                status=RuleResultStatus.ERROR,
                logic_result=None,
                message=f"Expression evaluation error: {exc}",
                deficiency=None,
                citation=rule.display_citation,
                needs_verification=rule.needs_verification,
                evidence_summaries=summaries,
                error=str(exc),
            )
        except (ValueError, TypeError, KeyError) as exc:
            return RuleResult(
                rule_id=rule.rule_id,
                title=rule.title,
                status=RuleResultStatus.ERROR,
                logic_result=None,
                message=f"Evaluation runtime error: {exc}",
                deficiency=None,
                citation=rule.display_citation,
                needs_verification=rule.needs_verification,
                evidence_summaries=summaries,
                error=str(exc),
            )

        # Logic evaluated; now apply trust gate
        if logic_result:
            has_indecisive_only = False
            if summaries:
                for s in summaries:
                    if s.best_trust_level in (TrustLevel.MODEL, TrustLevel.UNVERIFIED_CLAIM):
                        has_indecisive_only = True
                        break
            elif evidence_items and not any(e.is_decisive for e in evidence_items):
                has_indecisive_only = True

            if not gate_passes or has_indecisive_only:
                # Trust gate blocks PASS → UNVERIFIED
                blocked_types = [
                    s.required_type for s in summaries if not s.is_satisfied
                ]
                reason = (
                    f"Insufficient trust for: {blocked_types}."
                    if blocked_types
                    else "Evidence contains only non-decisive Model-level or self-attested items."
                )
                return RuleResult(
                    rule_id=rule.rule_id,
                    title=rule.title,
                    status=RuleResultStatus.UNVERIFIED,
                    logic_result=True,
                    message=(
                        f"Logic passes but evidence trust gate failed. "
                        f"{reason} "
                        f"Rule requires min_trust_level per evidence_requirements."
                    ),
                    deficiency=None,
                    citation=rule.display_citation,
                    needs_verification=rule.needs_verification,
                    evidence_summaries=summaries,
                )
            # PASS: logic True + trust gate satisfied
            return RuleResult(
                rule_id=rule.rule_id,
                title=rule.title,
                status=RuleResultStatus.PASS,
                logic_result=True,
                message="All conditions satisfied.",
                deficiency=None,
                citation=rule.display_citation,
                needs_verification=rule.needs_verification,
                evidence_summaries=summaries,
            )

        # Logic is False → FAIL
        deficiency = _render_deficiency(rule.deficiency_template, merged_facts)
        return RuleResult(
            rule_id=rule.rule_id,
            title=rule.title,
            status=RuleResultStatus.FAIL,
            logic_result=False,
            message=deficiency or "Rule condition not satisfied.",
            deficiency=deficiency,
            citation=rule.display_citation,
            needs_verification=rule.needs_verification,
            evidence_summaries=summaries,
        )

    def evaluate_all(
        self,
        rules: list[Rule],
        facts: dict[str, Any],
        evidence_items: list[EvidenceItem] | None = None,
    ) -> list[RuleResult]:
        """Evaluate all rules and return ordered list of results."""
        return [self.evaluate_one(r, facts, evidence_items) for r in rules]


# Module-level singleton
rule_engine = RuleEngine()
