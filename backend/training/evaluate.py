"""Evaluation script measuring field-level exact match (EM) and grounding rate.

Advisory ML Layer (Trust Ladder: Model).
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz

logger = logging.getLogger(__name__)


def normalize_value(val: Any) -> str:
    """Normalize values for comparison (stripping formatting, whitespace, lowercase)."""
    if val is None:
        return ""
    if isinstance(val, (int, float)):
        # Normalize numeric representation
        return f"{float(val):.4f}".rstrip("0").rstrip(".")
    s = str(val).strip().lower()
    s = re.sub(r"[\s\-_,\.;:/\(\)\[\]]+", " ", s)
    return s.strip()


def check_grounding_in_text(val: Any, text: str, threshold: float = 0.85) -> bool:
    """Check if value can be grounded in the context text with exact or fuzzy match."""
    if val is None:
        return False

    val_str = str(val).strip().lower()
    text_lower = text.lower()

    # 1. Direct substring check (e.g. "4.5", "10/2", "2026-05-15")
    if val_str and val_str in text_lower:
        return True

    # 2. Number normalization check (e.g. 4.5 vs 4.50)
    if isinstance(val, (int, float)):
        num_str = f"{float(val):.4f}".rstrip("0").rstrip(".")
        if num_str in text_lower:
            return True

    # 3. Normalized string and fuzzy token match
    norm_val = normalize_value(val)
    if not norm_val:
        return False

    norm_text = normalize_value(text)
    if norm_val in norm_text:
        return True

    score = fuzz.partial_ratio(norm_val, norm_text) / 100.0
    return score >= threshold


def evaluate_predictions(
    samples: list[dict[str, Any]],
    fuzzy_threshold: float = 0.85,
) -> dict[str, Any]:
    """Compute field-level exact match and grounding rate.

    Each sample should have:
      - 'input': document text
      - 'ground_truth': dict of expected field key-values
      - 'prediction': dict of predicted field key-values
    """
    total_fields = 0
    exact_matches = 0

    total_pred_fields = 0
    grounded_pred_fields = 0
    hallucinated_pred_fields = 0

    field_stats: dict[str, dict[str, int]] = {}

    for sample in samples:
        doc_text = sample.get("input", "")
        ground_truth = sample.get("ground_truth", {})
        prediction = sample.get("prediction", {})

        # 1. Exact Match on Ground Truth keys
        for key, expected_val in ground_truth.items():
            total_fields += 1
            if key not in field_stats:
                field_stats[key] = {
                    "total": 0,
                    "exact_matches": 0,
                    "pred_count": 0,
                    "grounded_count": 0,
                }
            field_stats[key]["total"] += 1

            pred_val = prediction.get(key)
            if pred_val is not None and normalize_value(pred_val) == normalize_value(expected_val):
                exact_matches += 1
                field_stats[key]["exact_matches"] += 1

        # 2. Grounding Rate on Predicted keys
        for key, pred_val in prediction.items():
            if pred_val is None:
                continue
            total_pred_fields += 1
            if key in field_stats:
                field_stats[key]["pred_count"] += 1

            is_grounded = check_grounding_in_text(pred_val, doc_text, threshold=fuzzy_threshold)
            if is_grounded:
                grounded_pred_fields += 1
                if key in field_stats:
                    field_stats[key]["grounded_count"] += 1
            else:
                hallucinated_pred_fields += 1

    em_rate = (exact_matches / total_fields) if total_fields > 0 else 0.0
    grounding_rate = (grounded_pred_fields / total_pred_fields) if total_pred_fields > 0 else 1.0
    hallucination_rate = (hallucinated_pred_fields / total_pred_fields) if total_pred_fields > 0 else 0.0

    field_breakdown = {}
    for key, stats in field_stats.items():
        tot = stats["total"]
        em = stats["exact_matches"]
        pred_c = stats["pred_count"]
        grnd_c = stats["grounded_count"]
        field_breakdown[key] = {
            "exact_match_rate": round(em / tot, 4) if tot > 0 else 0.0,
            "grounding_rate": round(grnd_c / pred_c, 4) if pred_c > 0 else 1.0,
            "total_instances": tot,
        }

    return {
        "summary": {
            "total_evaluated_samples": len(samples),
            "total_target_fields": total_fields,
            "exact_matches": exact_matches,
            "field_exact_match_rate": round(em_rate, 4),
            "total_predicted_fields": total_pred_fields,
            "grounded_predicted_fields": grounded_pred_fields,
            "hallucination_count": hallucinated_pred_fields,
            "grounding_rate": round(grounding_rate, 4),
            "hallucination_rate": round(hallucination_rate, 4),
        },
        "field_breakdown": field_breakdown,
    }


def print_evaluation_report(metrics: dict[str, Any]) -> None:
    """Format and print an evaluation summary table."""
    summary = metrics["summary"]
    breakdown = metrics.get("field_breakdown", {})

    print("\n" + "=" * 68)
    print("        NIRIKSHAN ADVISORY EXTRACTION EVALUATION REPORT          ")
    print("=" * 68)
    print(f"Total Evaluated Samples:      {summary['total_evaluated_samples']}")
    print(f"Field-Level Exact Match (EM): {summary['field_exact_match_rate'] * 100:.2f}%  ({summary['exact_matches']}/{summary['total_target_fields']})")
    print(f"Document Grounding Rate:      {summary['grounding_rate'] * 100:.2f}%  ({summary['grounded_predicted_fields']}/{summary['total_predicted_fields']})")
    print(f"Hallucination Rate:           {summary['hallucination_rate'] * 100:.2f}%  ({summary['hallucination_count']}/{summary['total_predicted_fields']})")
    print("-" * 68)
    print(f"{'Field Name':<28} | {'Exact Match':<14} | {'Grounding Rate':<14}")
    print("-" * 68)
    for field, stats in breakdown.items():
        em_pct = f"{stats['exact_match_rate'] * 100:.1f}%"
        grnd_pct = f"{stats['grounding_rate'] * 100:.1f}%"
        print(f"{field:<28} | {em_pct:<14} | {grnd_pct:<14}")
    print("=" * 68 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Field-Level Exact Match and Grounding Rate")
    parser.add_argument("--predictions", type=str, required=True, help="Path to jsonl file containing predictions and ground truth")
    parser.add_argument("--output-json", type=str, default=None, help="Optional output JSON path for metrics")
    parser.add_argument("--threshold", type=float, default=0.85, help="Fuzzy grounding threshold")
    args = parser.parse_args()

    pred_path = Path(args.predictions)
    if not pred_path.exists():
        print(f"Error: Predictions file not found: {pred_path}")
        return

    samples = []
    with pred_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                samples.append(json.loads(line))

    results = evaluate_predictions(samples, fuzzy_threshold=args.threshold)
    print_evaluation_report(results)

    if args.output_json:
        out_path = Path(args.output_json)
        out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"Metrics saved to {out_path}")


if __name__ == "__main__":
    main()
