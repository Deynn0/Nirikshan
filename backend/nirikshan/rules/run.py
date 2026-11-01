"""CLI runner: python -m nirikshan.rules.run --ruleset X --facts facts.json

Prints per-rule results with citations, trust gate status, and deficiencies.

Usage:
    python -m nirikshan.rules.run \\
        --ruleset aicte_aph_sample.yaml \\
        --facts facts.json \\
        [--year 2025-2026] \\
        [--evidence evidence.json] \\
        [--format text|json]
"""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from typing import Any

from nirikshan.rules.engine import RuleEngine, RuleResultStatus
from nirikshan.rules.loader import RulesetLoader
from nirikshan.trust.ladder import EvidenceItem

# ---------------------------------------------------------------------------
# ANSI colour helpers (disabled on non-TTY)
# ---------------------------------------------------------------------------

_USE_COLOR = sys.stdout.isatty()

_COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "green": "\033[32m",
    "red": "\033[31m",
    "yellow": "\033[33m",
    "cyan": "\033[36m",
    "magenta": "\033[35m",
    "grey": "\033[90m",
}


def _c(color: str, text: str) -> str:
    if not _USE_COLOR:
        return text
    return f"{_COLORS.get(color, '')}{text}{_COLORS['reset']}"


# ---------------------------------------------------------------------------
# Status formatting
# ---------------------------------------------------------------------------

_STATUS_COLOR = {
    RuleResultStatus.PASS: "green",
    RuleResultStatus.FAIL: "red",
    RuleResultStatus.UNVERIFIED: "yellow",
    RuleResultStatus.SKIP: "grey",
    RuleResultStatus.ERROR: "magenta",
}


_DIVIDER = "-" * 70


def _status_label(status: RuleResultStatus) -> str:
    labels = {
        RuleResultStatus.PASS: "[PASS]",
        RuleResultStatus.FAIL: "[FAIL]",
        RuleResultStatus.UNVERIFIED: "[UNVERIFIED]",
        RuleResultStatus.SKIP: "[SKIP]",
        RuleResultStatus.ERROR: "[ERROR]",
    }
    text = labels.get(status, status.value)
    return _c(_STATUS_COLOR.get(status, "reset"), text)


# ---------------------------------------------------------------------------
# Load helpers
# ---------------------------------------------------------------------------


def _load_facts(facts_path: str) -> dict[str, Any]:
    with open(facts_path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("facts.json must be a JSON object (dict)")
    return data


def _load_evidence(evidence_path: str | None) -> list[EvidenceItem]:
    if not evidence_path:
        return []
    with open(evidence_path, encoding="utf-8") as f:
        raw_list: list[dict[str, Any]] = json.load(f)
    return [EvidenceItem.model_validate(item) for item in raw_list]


# ---------------------------------------------------------------------------
# Text output
# ---------------------------------------------------------------------------

def _print_text_results(
    ruleset_file: str,
    sha256: str,
    year: str | None,
    results_with_rules: list[tuple[Any, Any]],
) -> None:
    print()
    print(_c("bold", f"  Nirikshan Rule Engine -- Ruleset: {ruleset_file}"))
    print(_c("grey", f"  SHA-256: {sha256}"))
    if year:
        print(_c("grey", f"  Filtered to academic year: {year}"))
    print()
    print(_DIVIDER)

    counts = dict.fromkeys(RuleResultStatus, 0)

    for _rule, result in results_with_rules:
        counts[result.status] += 1
        print()
        label = _status_label(result.status)
        print(f"  {label}  {_c('bold', result.rule_id)} - {result.title}")
        print(f"  {_c('grey', 'Citation:')} {result.citation}")
        if result.needs_verification:
            print(f"  {_c('yellow', '[NEEDS_VERIFICATION] Citation requires expert review')}")
        if result.message:
            print(f"  {_c('grey', 'Detail:')} {result.message}")
        if result.deficiency:
            print(f"  {_c('red', 'Deficiency:')} {result.deficiency}")
        if result.evidence_summaries:
            print(f"  {_c('grey', 'Evidence gate:')}")
            for ev in result.evidence_summaries:
                ok = _c("green", "[OK]") if ev.is_satisfied else _c("red", "[MISSING/LOW]")
                best = ev.best_trust_level or "none"
                print(
                    f"    {ok} {ev.required_type}: "
                    f"required={ev.min_trust_level}, best={best}"
                )
        print(_c("grey", "  " + _DIVIDER))

    print()
    print(_c("bold", "  Summary"))
    for status, count in counts.items():
        if count:
            print(f"    {_status_label(status)}: {count}")
    print()


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------


def _print_json_results(
    ruleset_file: str,
    sha256: str,
    year: str | None,
    results_with_rules: list[tuple[Any, Any]],
) -> None:
    output = {
        "ruleset": ruleset_file,
        "sha256": sha256,
        "academic_year_filter": year,
        "results": [
            {
                "rule_id": r.rule_id,
                "title": r.title,
                "status": r.status.value,
                "logic_result": r.logic_result,
                "message": r.message,
                "deficiency": r.deficiency,
                "citation": r.citation,
                "needs_verification": r.needs_verification,
                "evidence_gate": [
                    {
                        "type": e.required_type,
                        "min_trust_level": e.min_trust_level,
                        "best_trust_level": e.best_trust_level,
                        "satisfied": e.is_satisfied,
                    }
                    for e in r.evidence_summaries
                ],
            }
            for _, r in results_with_rules
        ],
    }
    print(json.dumps(output, indent=2, default=str))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        with contextlib.suppress(Exception):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        prog="python -m nirikshan.rules.run",
        description="Nirikshan deterministic rule engine CLI",
    )
    parser.add_argument(
        "--ruleset",
        required=True,
        help="YAML ruleset filename (relative to rulesets dir), e.g. aicte_aph_sample.yaml",
    )
    parser.add_argument(
        "--facts",
        required=True,
        help="Path to JSON facts file",
    )
    parser.add_argument(
        "--year",
        default=None,
        help="Filter rules by academic year, e.g. '2025-2026'",
    )
    parser.add_argument(
        "--evidence",
        default=None,
        help="Optional path to JSON evidence items file",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args(argv)

    # Load ruleset
    loader = RulesetLoader()
    try:
        meta = loader.load(args.ruleset)
    except Exception as exc:
        print(f"Error loading ruleset: {exc}", file=sys.stderr)
        return 1

    rules = meta.filter_by_year(args.year) if args.year else meta.rules

    if not rules:
        print(
            f"No rules found{f' for year {args.year!r}' if args.year else ''}.",
            file=sys.stderr,
        )
        return 1

    # Load facts
    try:
        facts = _load_facts(args.facts)
    except Exception as exc:
        print(f"Error loading facts: {exc}", file=sys.stderr)
        return 1

    # Load evidence (optional)
    try:
        evidence_items = _load_evidence(args.evidence)
    except Exception as exc:
        print(f"Error loading evidence: {exc}", file=sys.stderr)
        return 1

    # Evaluate
    engine = RuleEngine()
    results = engine.evaluate_all(rules, facts, evidence_items)
    pairs = list(zip(rules, results, strict=True))

    # Output
    if args.format == "json":
        _print_json_results(args.ruleset, meta.sha256_hash, args.year, pairs)
    else:
        _print_text_results(args.ruleset, meta.sha256_hash, args.year, pairs)

    # Exit code: 1 if any FAIL or UNVERIFIED
    bad = any(
        r.status in (RuleResultStatus.FAIL, RuleResultStatus.UNVERIFIED)
        for _, r in pairs
    )
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
