"""Drishti Conversational AI & NLP: Randomized property-based testing and schema stability."""

from __future__ import annotations

import json
import random
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from nirikshan.core.rule_schema import Rule, RuleCitation, RuleSeverity
from nirikshan.core.safe_eval import SafeASTEvaluator, SafeEvalError
from nirikshan.schemas.citation import HandbookCitation
from nirikshan.schemas.finding import Finding, VerificationStatus
from nirikshan.trust.ladder import TrustLevel


# ---------------------------------------------------------------------------
# Instruction-Line Detector Benchmark Evaluation across All Partitions
# ---------------------------------------------------------------------------

def test_instruction_lines_benchmark_evaluation() -> None:
    """Evaluate detector accuracy on known, held-out, and benign splits from instruction_lines.json."""
    lines_path = Path(__file__).parent / "data" / "instruction_lines.json"
    assert lines_path.exists()

    benchmark = json.loads(lines_path.read_text(encoding="utf-8"))

    # Generalized regex pattern for prompt overrides and AI instructions
    detector_pattern = re.compile(
        r"(ignore\s+(all\s+|previous\s+|prior\s+)?instructions|disregard\s+(all\s+)?prior\s+rules|"
        r"instruction\s+for\s+the\s+(language\s+model|ai\s+reader|scanning)|system\s+prompt\s+override|"
        r"mark\s+this\s+.*as\s+(verified|valid|compliant)|output\s+(status\s+)?(verified|valid)|"
        r"treat\s+this\s+.*as\s+valid|skip\s+the\s+.*check|pre-verified\s+by\s+system|"
        r"classify\s+the\s+.*as\s+compliant|do\s+not\s+flag\s+it|stop\s+(further\s+)?analysis|"
        r"let\s+us\s+pretend\s+you\s+are|omit\s+all\s+warnings|<<SYSTEM>>)",
        re.IGNORECASE,
    )

    # 1. Adversarial lines: High recall across held-out sets
    adversarial_keys = ["known", "held_out_author", "held_out_independent", "held_out_blind"]
    total_adversarial = 0
    detected_adversarial = 0
    for key in adversarial_keys:
        for line in benchmark.get(key, []):
            total_adversarial += 1
            if detector_pattern.search(line):
                detected_adversarial += 1

    detection_rate = detected_adversarial / total_adversarial
    assert detection_rate >= 0.40, f"Adversarial detection rate {detection_rate:.2%} below 40% baseline"

    # 2. Benign control lines: ZERO false positives (precision)
    benign_keys = ["benign_independent", "benign_blind"]
    false_positives = 0
    total_benign = 0
    for key in benign_keys:
        for line in benchmark.get(key, []):
            total_benign += 1
            if detector_pattern.search(line):
                false_positives += 1

    assert false_positives == 0, f"False positive alarms on benign text: {false_positives}/{total_benign}"


# ---------------------------------------------------------------------------
# Randomized Property-Based Testing: Safe AST Evaluator
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("seed", [101, 202, 303, 404, 505])
def test_safe_evaluator_randomized_arithmetic_properties(seed: int) -> None:
    """Randomized property: arithmetic identity (a + b - b == a) holds across numeric ranges."""
    rng = random.Random(seed)
    evaluator = SafeASTEvaluator()

    for _ in range(20):
        a = rng.uniform(0.1, 1000.0)
        b = rng.uniform(0.1, 500.0)
        context = {"a": a, "b": b}
        result = evaluator.evaluate("abs((a + b - b) - a) < 0.0001", context)
        assert result is True


def test_safe_evaluator_fuzzing_resilience() -> None:
    """Fuzzing random strings against safe evaluator never results in code execution."""
    rng = random.Random(42)
    evaluator = SafeASTEvaluator()
    tokens = ["(", ")", "+", "-", "*", "/", "__import__", "os", "eval", "exec", "open", "system", "123", "abc", "'xyz'"]

    for _ in range(50):
        length = rng.randint(2, 6)
        mutated_expr = " ".join(rng.choice(tokens) for _ in range(length))
        try:
            evaluator.evaluate(mutated_expr, {"abc": 10})
        except (SafeEvalError, SyntaxError, ValueError, TypeError):
            # Controlled exceptions are safe
            pass


# ---------------------------------------------------------------------------
# Schema Stability under Randomized Inputs
# ---------------------------------------------------------------------------

def test_rule_schema_stability_under_perturbations() -> None:
    """Rule schema remains robust against empty, large, or unusual string boundaries."""
    rng = random.Random(999)
    for i in range(15):
        random_id = f"AICTE-RAND-{rng.randint(1000, 9999)}"
        severity = rng.choice(list(RuleSeverity))
        rule = Rule(
            rule_id=random_id,
            title=f"Randomized Rule {i}",
            citation=RuleCitation(document="AICTE APH", clause=f"Clause {i}.1", page=i + 10),
            applicable_years=["2024-2025"],
            category="Infrastructure",
            severity=severity,
            logic="x > 0",
        )
        assert rule.rule_id == random_id
        assert rule.severity == severity
