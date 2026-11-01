"""Unit tests for Phase 1: Rule schema, Safe Evaluator, Trust-Level Gating,
Alias Matching (English + Hindi), Ruleset Hashing, and Academic Year Filtering.
"""

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from nirikshan.core.rule_schema import (
    EvidenceRequirement,
    Rule,
    RuleCitation,
    RuleSeverity,
)
from nirikshan.core.safe_eval import SafeASTEvaluator, SafeEvalError
from nirikshan.rules.aliases import AliasResolver, normalize_devanagari
from nirikshan.rules.engine import RuleEngine, RuleResultStatus
from nirikshan.rules.loader import RulesetLoader
from nirikshan.trust.ladder import EvidenceItem, TrustLevel

# ===========================================================================
# 1. Rule Schema Validation Tests
# ===========================================================================


def test_rule_schema_valid_instantiation() -> None:
    """Valid Rule object instantiates correctly with all required fields."""
    rule = Rule(
        rule_id="AICTE-TEST-001",
        title="Test Fire Safety Rule",
        citation=RuleCitation(
            document="AICTE Approval Process Handbook 2024-2027",
            clause="Clause 6.1",
            page=60,
            edition="2024-2027",
            needs_verification=False,
        ),
        applicable_years=["2024-2025", "2025-2026"],
        category="Safety & Compliance",
        evidence_requirements=[
            EvidenceRequirement(type="FIRE_SAFETY_NOC", min_trust_level="ISSUER")
        ],
        logic="fire_noc_valid == True",
        severity=RuleSeverity.CRITICAL,
        deficiency_template="Fire NOC invalid: {fire_noc_valid}",
        needs_verification=False,
    )
    assert rule.rule_id == "AICTE-TEST-001"
    assert rule.severity == RuleSeverity.CRITICAL
    assert rule.needs_verification is False
    assert "Clause 6.1" in rule.display_citation
    assert "p.60" in rule.display_citation


def test_rule_schema_invalid_id_raises() -> None:
    """Invalid rule_id patterns must raise ValidationError."""
    with pytest.raises(ValidationError):
        Rule(
            rule_id="lower_case_id_not_allowed!",
            title="Bad Rule",
            citation=RuleCitation(document="Doc", clause="1", page=1),
            applicable_years=["2024-2025"],
            category="Test",
        )


def test_rule_schema_invalid_trust_level_raises() -> None:
    """Non-existent min_trust_level string must be rejected."""
    with pytest.raises(ValidationError):
        EvidenceRequirement(type="DOC_X", min_trust_level="SUPER_TRUST")


def test_citation_needs_verification_escalates_to_rule() -> None:
    """If citation has needs_verification=True, rule inherits needs_verification=True."""
    rule = Rule(
        rule_id="AICTE-TODO-001",
        title="Draft Rule with Placeholder Citation",
        citation=RuleCitation(
            document="AICTE Handbook (Draft)",
            clause="Clause 99.9",
            page="TODO",
            needs_verification=True,
        ),
        applicable_years=["2024-2025"],
        category="Draft",
        needs_verification=False,  # Should be overridden by model_validator
    )
    assert rule.needs_verification is True


# ===========================================================================
# 2. Safe Expression Evaluator & Injection Defense Tests
# ===========================================================================


def test_safe_eval_comparisons_and_arithmetic() -> None:
    """Test comparisons, boolean ops, arithmetic, and set membership."""
    evaluator = SafeASTEvaluator()
    facts = {
        "land_area": 3.5,
        "min_area": 2.5,
        "is_contiguous": True,
        "category": "Urban",
        "roles": ["UG", "PG"],
    }

    assert evaluator.evaluate("land_area >= min_area and is_contiguous == True", facts) is True
    assert evaluator.evaluate("land_area < 2.0 or not is_contiguous", facts) is False
    assert evaluator.evaluate("category in ['Urban', 'Metro']", facts) is True
    assert evaluator.evaluate("category not in ['Rural']", facts) is True
    assert evaluator.evaluate("10 * 2 + 5 == 25", facts) is True


def test_safe_eval_date_arithmetic() -> None:
    """Test built-in date helper functions in expressions."""
    evaluator = SafeASTEvaluator()
    future = (date.today() + timedelta(days=100)).strftime("%Y-%m-%d")
    past = (date.today() - timedelta(days=100)).strftime("%Y-%m-%d")

    assert evaluator.evaluate(f"days_until('{future}') > 0", {}) is True
    assert evaluator.evaluate(f"days_until('{past}') < 0", {}) is True
    assert evaluator.evaluate("date_diff('2025-01-01', '2025-01-11', 'days') == 10", {}) is True


@pytest.mark.parametrize(
    "payload",
    [
        "__import__('os').system('dir')",
        "__import__('subprocess').call(['calc'])",
        "open('secret.txt').read()",
        "(lambda: 1)()",
        "[c for c in ().__class__.__bases__[0].__subclasses__() if c.__name__ == 'catch_warnings']",
        "eval('1 + 1')",
        "exec('x = 1')",
        "__builtins__['dir']()",
        "obj._private_attr",
        "str.upper('hello')",
    ],
)
def test_safe_evaluator_blocks_code_injection(payload: str) -> None:
    """Any attempt to call unauthorized functions, access private attributes, or execute shell commands must fail."""
    evaluator = SafeASTEvaluator()
    with pytest.raises((SafeEvalError, ValueError)):
        evaluator.evaluate(payload, {"obj": object()})


# ===========================================================================
# 3. Trust-Level Gating Tests
# ===========================================================================


def _create_evidence(
    doc_type: str,
    trust_level: TrustLevel,
    is_self_attested: bool = False,
    is_tampered: bool = False,
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id="ev-001",
        trust_level=trust_level,
        source_type=doc_type,
        description="Test evidence item",
        source_document_id="doc-001",
        source_document_name="test.pdf",
        verification_method="TEST_VERIFIER",
        is_self_attested=is_self_attested,
        is_tampered=is_tampered,
    )


def test_trust_gate_allows_pass_when_trust_satisfied() -> None:
    """Logic passes and evidence >= min_trust_level -> PASS."""
    rule = Rule(
        rule_id="AICTE-GATE-001",
        title="Fire NOC Rule",
        citation=RuleCitation(document="Doc", clause="1", page=1),
        applicable_years=["2024-2025"],
        category="Safety",
        evidence_requirements=[
            EvidenceRequirement(type="FIRE_SAFETY_NOC", min_trust_level="ISSUER")
        ],
        logic="fire_noc_valid == True",
    )
    engine = RuleEngine()
    ev = [_create_evidence("FIRE_SAFETY_NOC", TrustLevel.ISSUER)]
    result = engine.evaluate_one(rule, {"fire_noc_valid": True}, ev)

    assert result.status == RuleResultStatus.PASS
    assert result.logic_result is True


def test_trust_gate_returns_unverified_when_trust_insufficient() -> None:
    """Logic passes but evidence is BELOW min_trust_level -> UNVERIFIED (NEVER PASS)."""
    rule = Rule(
        rule_id="AICTE-GATE-002",
        title="Fire NOC Rule Requiring Issuer Trust",
        citation=RuleCitation(document="Doc", clause="1", page=1),
        applicable_years=["2024-2025"],
        category="Safety",
        evidence_requirements=[
            EvidenceRequirement(type="FIRE_SAFETY_NOC", min_trust_level="ISSUER")
        ],
        logic="fire_noc_valid == True",
    )
    engine = RuleEngine()
    # Provided MODEL trust (Rank 10) which is below ISSUER (Rank 50)
    ev = [_create_evidence("FIRE_SAFETY_NOC", TrustLevel.MODEL)]
    result = engine.evaluate_one(rule, {"fire_noc_valid": True}, ev)

    assert result.status == RuleResultStatus.UNVERIFIED
    assert result.logic_result is True
    assert "Insufficient trust" in result.message


def test_self_attestation_collapses_trust_gate_blocks_pass() -> None:
    """Applicant self-attestation collapses to UNVERIFIED_CLAIM, blocking PASS."""
    rule = Rule(
        rule_id="AICTE-GATE-003",
        title="Land Area Rule",
        citation=RuleCitation(document="Doc", clause="1", page=1),
        applicable_years=["2024-2025"],
        category="Land",
        evidence_requirements=[
            EvidenceRequirement(type="LAND_SALE_DEED", min_trust_level="RECORD")
        ],
        logic="land_area_acres >= 2.5",
    )
    engine = RuleEngine()
    # Claimed RECORD level, but self-attested
    ev = [
        _create_evidence(
            "LAND_SALE_DEED", TrustLevel.RECORD, is_self_attested=True
        )
    ]
    result = engine.evaluate_one(rule, {"land_area_acres": 5.0}, ev)

    assert result.status == RuleResultStatus.UNVERIFIED
    assert result.logic_result is True


def test_rule_fail_renders_deficiency_template() -> None:
    """When logic evaluates to False, status is FAIL and deficiency_template is rendered."""
    rule = Rule(
        rule_id="AICTE-GATE-004",
        title="Minimum Land Area",
        citation=RuleCitation(document="Doc", clause="1", page=1),
        applicable_years=["2024-2025"],
        category="Land",
        evidence_requirements=[
            EvidenceRequirement(type="LAND_SALE_DEED", min_trust_level="RECORD")
        ],
        parameters={"required_acres": 2.5},
        logic="land_area_acres >= required_acres",
        deficiency_template="Requires {required_acres} acres; only {land_area_acres} acres possessed.",
    )
    engine = RuleEngine()
    ev = [_create_evidence("LAND_SALE_DEED", TrustLevel.RECORD)]
    result = engine.evaluate_one(rule, {"land_area_acres": 1.8}, ev)

    assert result.status == RuleResultStatus.FAIL
    assert result.logic_result is False
    assert result.deficiency == "Requires 2.5 acres; only 1.8 acres possessed."


# ===========================================================================
# 4. Alias Dictionaries & Fuzzy Matching Tests
# ===========================================================================


def test_alias_english_exact_and_fuzzy() -> None:
    """English label variants match exact and fuzzy canonical fields."""
    resolver = AliasResolver()
    resolver.reload()

    # Exact match
    assert resolver.resolve("Total Land Area") == "land_area_acres"
    assert resolver.resolve("Fire Safety Certificate Valid") == "fire_noc_valid"

    # Fuzzy match with slight variations
    assert resolver.resolve("Total land in acre") == "land_area_acres"
    assert resolver.resolve("Fire safety NOC status") == "fire_noc_valid"


def test_alias_hindi_exact_fuzzy_and_devanagari_normalization() -> None:
    """Hindi label variants match with Devanagari normalization."""
    resolver = AliasResolver()
    resolver.reload()

    # Exact Hindi
    assert resolver.resolve("भूमि का क्षेत्रफल (एकड़)") == "land_area_acres"
    assert resolver.resolve("अग्निशमन अनापत्ति प्रमाण पत्र वैध") == "fire_noc_valid"

    # Zero-width characters stripped
    zw_text = "अग्निशमन\u200b अनापत्ति प्रमाण पत्र वैध"
    assert normalize_devanagari(zw_text) == "अग्निशमन अनापत्ति प्रमाण पत्र वैध"
    assert resolver.resolve(zw_text) == "fire_noc_valid"

    # Fuzzy Hindi match
    assert resolver.resolve("अग्नि सुरक्षा एनओसी स्थिति") == "fire_noc_valid"


def test_alias_unknown_label_returns_none() -> None:
    """Completely unresolvable label returns None."""
    resolver = AliasResolver()
    resolver.reload()
    assert resolver.resolve("xyz123 completely unrelated label") is None


# ===========================================================================
# 5. Ruleset Loader, SHA-256 Hash, and Year Filtering Tests
# ===========================================================================


def test_ruleset_loader_loads_sample_and_computes_sha256() -> None:
    """Sample YAML loads, validates, and has valid 64-char SHA-256 hash."""
    loader = RulesetLoader()
    meta = loader.load("aicte_aph_sample.yaml")

    assert len(meta.rules) >= 10
    assert len(meta.sha256_hash) == 64
    assert all(c in "0123456789abcdef" for c in meta.sha256_hash)
    assert meta.version == "2024-2027-sample"


def test_ruleset_year_filtering() -> None:
    """Ruleset filters correctly by academic year."""
    loader = RulesetLoader()
    rules_2025 = loader.filter_by_year("aicte_aph_sample.yaml", "2025-2026")
    assert len(rules_2025) >= 10

    # Nonexistent academic year returns empty list
    rules_none = loader.filter_by_year("aicte_aph_sample.yaml", "1990-1991")
    assert len(rules_none) == 0
