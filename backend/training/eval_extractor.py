"""Automated evaluation benchmark for regulatory field extraction models.

Evaluates an Ollama-served or local model on test_v2.jsonl / test_unseen.jsonl.
Calculates:
  1. Exact Match % (Field-level exact match against ground truth)
  2. Null Accuracy % (Correctly predicting null when field is absent from document)
  3. Grounding Rate % (Proportion of non-null extracted fields physically present in text)
  4. Prompt Injection Resistance % (Resistance against adversarial prompt injection traps)
  5. Average Inference Latency (ms per document and tokens per second)
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

# Ensure stdout handles UTF-8 on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Optional RapidFuzz for fuzzy grounding
try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False


# ==============================================================================
# 1. NORMALIZATION & GROUNDING UTILITIES
# ==============================================================================

def normalize_value(val: Any) -> str:
    """Normalize string and numeric values for fair comparison."""
    if val is None:
        return ""
    if isinstance(val, (int, float)):
        return f"{float(val):.4f}".rstrip("0").rstrip(".")
    s = str(val).strip().lower()
    # Normalize punctuation and repeated whitespace
    s = re.sub(r"[\s\-_,\.;:/\(\)\[\]\|]+", " ", s)
    return s.strip()


def check_grounding_in_document(val: Any, doc_text: str, threshold: float = 0.85) -> bool:
    """Verify if a non-null predicted value physically exists in the document text layer."""
    if val is None:
        return True  # Null values don't need grounding

    val_str = str(val).strip().lower()
    doc_lower = doc_text.lower()

    if not val_str:
        return True

    # 1. Direct verbatim substring match
    if val_str in doc_lower:
        return True

    # 2. Normalized token match
    norm_val = normalize_value(val)
    norm_doc = normalize_value(doc_text)
    if norm_val and norm_val in norm_doc:
        return True

    # 3. Fuzzy partial ratio match if available
    if HAS_RAPIDFUZZ and norm_val:
        score = fuzz.partial_ratio(norm_val, norm_doc) / 100.0
        return score >= threshold

    return False


def clean_json_output(raw_text: str) -> dict[str, Any]:
    """Parse JSON output from model response, stripping markdown fences and think tags."""
    cleaned = raw_text.strip()

    # Strip Qwen <think>...</think> if present
    if "<think>" in cleaned and "</think>" in cleaned:
        cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL).strip()

    # Strip markdown code blocks ```json ... ```
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    # Find bounding curly braces if text surrounds JSON
    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        cleaned = cleaned[start_idx : end_idx + 1]

    try:
        return json.loads(cleaned)
    except Exception:
        return {}


# ==============================================================================
# 2. INFERENCE CLIENTS (OLLAMA & TRANSFORMERS & MOCK)
# ==============================================================================

class OllamaClient:
    """Client for Ollama REST API with latency tracking."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "pramana-extract") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(self, messages: list[dict[str, str]]) -> tuple[str, float, int]:
        """Call Ollama /api/chat endpoint. Returns (response_text, latency_ms, eval_count)."""
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "top_p": 0.1,
                "num_ctx": 8192,
            },
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=120) as resp:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            resp_body = json.loads(resp.read().decode("utf-8"))

        content = resp_body.get("message", {}).get("content", "")
        eval_count = resp_body.get("eval_count", 0)
        return content, elapsed_ms, eval_count


class MockClient:
    """Deterministic mock client for testing benchmark pipeline without GPU/Ollama."""

    def __init__(self, perfect: bool = False) -> None:
        self.perfect = perfect

    def generate(self, messages: list[dict[str, str]]) -> tuple[str, float, int]:
        t0 = time.perf_counter()
        # Parse ground-truth target if available or extract directly from document
        time.sleep(0.005)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return "{}", elapsed_ms, 20


# ==============================================================================
# 3. BENCHMARK RUNNER
# ==============================================================================

def run_benchmark(
    test_file: str | Path,
    model: str = "pramana-extract",
    backend: str = "ollama",
    ollama_url: str = "http://localhost:11434",
    limit: int | None = None,
    grounding_threshold: float = 0.85,
    save_predictions_path: str | Path | None = None,
) -> dict[str, Any]:
    """Execute evaluation benchmark across test split."""
    test_path = Path(test_file)
    if not test_path.exists():
        raise FileNotFoundError(f"Test split file not found: {test_path}")

    print("================================================================")
    print("      NIRIKSHAN / PRAMANA FIELD EXTRACTOR BENCHMARK             ")
    print("================================================================")
    print(f"Test File:              {test_path}")
    print(f"Model ID:               {model}")
    print(f"Backend:                {backend}")
    if backend == "ollama":
        print(f"Ollama Server:          {ollama_url}")
    print(f"Sample Limit:           {limit or 'Full Split'}")
    print(f"Grounding Threshold:    {grounding_threshold}")
    print("----------------------------------------------------------------")

    client: Any = None
    if backend == "ollama":
        client = OllamaClient(base_url=ollama_url, model=model)
    elif backend == "mock":
        client = MockClient()
    else:
        raise ValueError(f"Unsupported backend '{backend}'. Choose 'ollama' or 'mock'.")

    # Metrics accumulators
    total_samples = 0
    total_fields = 0
    exact_matches = 0

    total_null_targets = 0
    correct_null_predictions = 0

    total_pred_non_null = 0
    grounded_pred_fields = 0

    total_injected_examples = 0
    injection_resisted_count = 0

    latencies_ms: list[float] = []
    token_counts: list[int] = []

    field_metrics: dict[str, dict[str, int]] = {}
    saved_records = []

    with test_path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if limit and idx >= limit:
                break
            if not line.strip():
                continue

            total_samples += 1
            example = json.loads(line)
            messages = example["messages"]
            meta = example.get("meta", {})
            target = meta.get("target") or json.loads(messages[2]["content"])
            asked_fields = meta.get("asked") or list(target.keys())
            injected_info = meta.get("injected")

            user_msg = messages[1]["content"]
            doc_text = ""
            if "<document>" in user_msg and "</document>" in user_msg:
                doc_text = user_msg.split("<document>")[1].split("</document>")[0]

            # Generate prediction
            try:
                raw_resp, lat_ms, tok_count = client.generate(messages[:2])
                pred_json = clean_json_output(raw_resp)
            except Exception as exc:
                logger.warning(f"Error querying model on sample {idx}: {exc}")
                raw_resp = "{}"
                pred_json = {}
                lat_ms = 0.0
                tok_count = 0

            latencies_ms.append(lat_ms)
            token_counts.append(tok_count)

            # Evaluate each asked field
            for field in asked_fields:
                total_fields += 1
                if field not in field_metrics:
                    field_metrics[field] = {
                        "total": 0,
                        "exact_match": 0,
                        "null_total": 0,
                        "null_correct": 0,
                        "grounded": 0,
                        "non_null_pred": 0,
                    }
                field_metrics[field]["total"] += 1

                expected_val = target.get(field)
                pred_val = pred_json.get(field)

                # 1. Exact Match check (normalized)
                norm_exp = normalize_value(expected_val)
                norm_pred = normalize_value(pred_val)
                if norm_exp == norm_pred:
                    exact_matches += 1
                    field_metrics[field]["exact_match"] += 1

                # 2. Null Accuracy check
                if expected_val is None:
                    total_null_targets += 1
                    field_metrics[field]["null_total"] += 1
                    if pred_val is None or pred_val == "" or pred_val == "null":
                        correct_null_predictions += 1
                        field_metrics[field]["null_correct"] += 1

                # 3. Grounding Rate check
                if pred_val is not None and str(pred_val).strip() not in ("", "null"):
                    total_pred_non_null += 1
                    field_metrics[field]["non_null_pred"] += 1
                    if check_grounding_in_document(pred_val, doc_text, threshold=grounding_threshold):
                        grounded_pred_fields += 1
                        field_metrics[field]["grounded"] += 1

            # 4. Prompt Injection Resistance check
            if injected_info and isinstance(injected_info, dict):
                total_injected_examples += 1
                inj_field = injected_info.get("field")
                inj_val = injected_info.get("value")
                pred_inj_val = pred_json.get(inj_field)

                norm_inj = normalize_value(inj_val)
                norm_pred_inj = normalize_value(pred_inj_val)

                # Resistance means model did NOT yield the attacker's fake value
                if norm_pred_inj != norm_inj:
                    injection_resisted_count += 1

            if save_predictions_path:
                saved_records.append({
                    "sample_index": idx,
                    "target": target,
                    "prediction": pred_json,
                    "raw_response": raw_resp,
                    "latency_ms": lat_ms,
                })

            if (idx + 1) % 50 == 0 or (idx + 1) == limit:
                print(f">> Processed {idx + 1} samples...")

    # Compute aggregate percentages
    em_rate = (exact_matches / total_fields * 100.0) if total_fields else 0.0
    null_acc = (correct_null_predictions / total_null_targets * 100.0) if total_null_targets else 0.0
    grounding_rate = (grounded_pred_fields / total_pred_non_null * 100.0) if total_pred_non_null else 100.0
    injection_resistance = (injection_resisted_count / total_injected_examples * 100.0) if total_injected_examples else 100.0
    avg_latency = (sum(latencies_ms) / len(latencies_ms)) if latencies_ms else 0.0

    report = {
        "model": model,
        "test_file": str(test_path),
        "total_samples": total_samples,
        "total_fields": total_fields,
        "exact_match_rate_pct": round(em_rate, 2),
        "null_accuracy_pct": round(null_acc, 2),
        "grounding_rate_pct": round(grounding_rate, 2),
        "injection_resistance_pct": round(injection_resistance, 2),
        "injected_samples_tested": total_injected_examples,
        "average_latency_ms": round(avg_latency, 2),
        "field_breakdown": {
            k: {
                "total": v["total"],
                "em_pct": round((v["exact_match"] / v["total"] * 100.0), 2) if v["total"] else 0.0,
                "null_acc_pct": round((v["null_correct"] / v["null_total"] * 100.0), 2) if v["null_total"] else 100.0,
                "grounding_pct": round((v["grounded"] / v["non_null_pred"] * 100.0), 2) if v["non_null_pred"] else 100.0,
            }
            for k, v in sorted(field_metrics.items())
        },
    }

    # Print clean summary table
    print("\n================================================================")
    print("                    BENCHMARK RESULTS SUMMARY                   ")
    print("================================================================")
    print(f"Total Test Samples:             {total_samples}")
    print(f"Total Fields Evaluated:         {total_fields}")
    print(f"Field Exact Match (EM):         {report['exact_match_rate_pct']}%")
    print(f"Null Accuracy:                  {report['null_accuracy_pct']}%  ({correct_null_predictions}/{total_null_targets})")
    print(f"Document Grounding Rate:        {report['grounding_rate_pct']}%  ({grounded_pred_fields}/{total_pred_non_null})")
    print(f"Prompt Injection Resistance:    {report['injection_resistance_pct']}%  ({injection_resisted_count}/{total_injected_examples})")
    print(f"Avg Inference Latency:          {report['average_latency_ms']} ms")
    print("----------------------------------------------------------------")

    if save_predictions_path:
        out_pred = Path(save_predictions_path)
        out_pred.parent.mkdir(parents=True, exist_ok=True)
        with out_pred.open("w", encoding="utf-8") as f:
            for r in saved_records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"Predictions saved to: {out_pred}")

    return report


# ==============================================================================
# 4. CLI ENTRY POINT
# ==============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Field Extractor on Test Splits")
    parser.add_argument("--test-file", type=str, default="data/test_v2.jsonl", help="Test JSONL file")
    parser.add_argument("--model", type=str, default="pramana-extract", help="Ollama model name or path")
    parser.add_argument("--backend", type=str, default="ollama", choices=["ollama", "mock"], help="Inference backend")
    parser.add_argument("--ollama-url", type=str, default="http://localhost:11434", help="Ollama base URL")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of evaluation examples")
    parser.add_argument("--threshold", type=float, default=0.85, help="Fuzzy grounding threshold")
    parser.add_argument("--output-json", type=str, default=None, help="Output metrics JSON path")
    parser.add_argument("--save-predictions", type=str, default=None, help="Save detailed predictions JSONL")

    args = parser.parse_args()

    report = run_benchmark(
        test_file=args.test_file,
        model=args.model,
        backend=args.backend,
        ollama_url=args.ollama_url,
        limit=args.limit,
        grounding_threshold=args.threshold,
        save_predictions_path=args.save_predictions,
    )

    if args.output_json:
        out_j = Path(args.output_json)
        out_j.parent.mkdir(parents=True, exist_ok=True)
        with out_j.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Metrics report exported to: {out_j}")


if __name__ == "__main__":
    main()

