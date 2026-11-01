"""Deterministic rule engine and ruleset orchestration."""

from nirikshan.rules.aliases import AliasResolver, alias_resolver, normalize_devanagari
from nirikshan.rules.engine import (
    EvidenceSummary,
    RuleEngine,
    RuleResult,
    RuleResultStatus,
    rule_engine,
)
from nirikshan.rules.loader import RulesetLoader, ruleset_loader

__all__ = [
    "AliasResolver",
    "EvidenceSummary",
    "RuleEngine",
    "RuleResult",
    "RuleResultStatus",
    "RulesetLoader",
    "alias_resolver",
    "normalize_devanagari",
    "rule_engine",
    "ruleset_loader",
]
