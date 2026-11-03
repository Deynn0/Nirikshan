"""Benchmark evaluation script for Drishti multilingual intent classifier.

Evaluates an Ollama-served or mock intent model on handwritten_test.jsonl.
Calculates:
  1. Overall Intent Classification Accuracy %
  2. Per-intent Precision and Recall
  3. Out-of-scope Detection and Rejection Rate %
  4. Average Inference Latency (ms)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

from lexicon import INTENTS

# Ensure stdout handles UTF-8 on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def clean_intent_json(raw: str) -> dict[str, Any]:
    """Parse JSON intent payload."""
    cleaned = raw.strip()
    if "<think>" in cleaned and "</think>" in cleaned:
        cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL).strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]
    try:
        return json.loads(cleaned)
    except Exception:
        return {}


def evaluate_drishti(
    test_file: str | Path = "handwritten_test.jsonl",
    model: str = "drishti-intent",
    ollama_url: str = "http://localhost:11434",
    backend: str = "ollama",
    limit: int | None = None,
    output_json: str | Path | None = None,
) -> dict[str, Any]:
    """Run intent classification benchmark."""
    test_path = Path(test_file)
    if not test_path.exists():
        raise FileNotFoundError(f"Test file not found: {test_path}")

    print("================================================================")
    print("           DRISHTI INTENT CLASSIFIER BENCHMARK                  ")
    print("================================================================")
    print(f"Test File:              {test_path}")
    print(f"Model ID:               {model}")
    print(f"Backend:                {backend}")
    print(f"Sample Limit:           {limit or 'Full Split'}")
    print("----------------------------------------------------------------")

    total_samples = 0
    correct_samples = 0
    out_of_scope_total = 0
    out_of_scope_correct = 0
    latencies_ms: list[float] = []

    intent_stats = {k: {"tp": 0, "fp": 0, "fn": 0, "total": 0} for k in INTENTS}

    with test_path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if limit and idx >= limit:
                break
            if not line.strip():
                continue

            total_samples += 1
            ex = json.loads(line)
            target = ex.get("meta", {}).get("target") or json.loads(ex["messages"][2]["content"])
            expected_intent = target.get("intent")
            if expected_intent in intent_stats:
                intent_stats[expected_intent]["total"] += 1
            if expected_intent == "out_of_scope":
                out_of_scope_total += 1

            if backend == "ollama":
                url = f"{ollama_url.rstrip('/')}/api/chat"
                payload = {
                    "model": model,
                    "messages": ex["messages"][:2],
                    "stream": False,
                    "options": {"temperature": 0.0, "num_ctx": 2048},
                }
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
                t0 = time.perf_counter()
                try:
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        lat_ms = (time.perf_counter() - t0) * 1000.0
                        body = json.loads(resp.read().decode("utf-8"))
                        raw_content = body.get("message", {}).get("content", "")
                        pred_json = clean_intent_json(raw_content)
                except Exception:
                    lat_ms = 0.0
                    pred_json = {}
            else:  # mock
                t0 = time.perf_counter()
                time.sleep(0.002)
                lat_ms = (time.perf_counter() - t0) * 1000.0
                pred_json = {"intent": expected_intent}  # Mock perfect response

            latencies_ms.append(lat_ms)
            pred_intent = pred_json.get("intent")

            if pred_intent == expected_intent:
                correct_samples += 1
                if expected_intent in intent_stats:
                    intent_stats[expected_intent]["tp"] += 1
                if expected_intent == "out_of_scope":
                    out_of_scope_correct += 1
            else:
                if expected_intent in intent_stats:
                    intent_stats[expected_intent]["fn"] += 1
                if pred_intent in intent_stats:
                    intent_stats[pred_intent]["fp"] += 1

    acc = (correct_samples / total_samples * 100.0) if total_samples else 0.0
    oos_acc = (out_of_scope_correct / out_of_scope_total * 100.0) if out_of_scope_total else 100.0
    avg_lat = (sum(latencies_ms) / len(latencies_ms)) if latencies_ms else 0.0

    report = {
        "model": model,
        "test_file": str(test_path),
        "total_samples": total_samples,
        "overall_accuracy_pct": round(acc, 2),
        "out_of_scope_rejection_pct": round(oos_acc, 2),
        "average_latency_ms": round(avg_lat, 2),
        "intent_breakdown": {
            k: {
                "support": v["total"],
                "precision": round(v["tp"] / (v["tp"] + v["fp"]) * 100.0, 2) if (v["tp"] + v["fp"]) else 0.0,
                "recall": round(v["tp"] / (v["tp"] + v["fn"]) * 100.0, 2) if (v["tp"] + v["fn"]) else 0.0,
            }
            for k, v in sorted(intent_stats.items())
        },
    }

    print("\n================================================================")
    print("                    BENCHMARK RESULTS SUMMARY                   ")
    print("================================================================")
    print(f"Total Test Samples:             {total_samples}")
    print(f"Overall Intent Accuracy:        {report['overall_accuracy_pct']}%")
    print(f"Out-of-Scope Rejection Rate:    {report['out_of_scope_rejection_pct']}%  ({out_of_scope_correct}/{out_of_scope_total})")
    print(f"Avg Inference Latency:          {report['average_latency_ms']} ms")
    print("----------------------------------------------------------------")

    if output_json:
        out_p = Path(output_json)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with out_p.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Metrics saved to: {out_p}")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Drishti Intent Classifier")
    parser.add_argument("--test-file", type=str, default="handwritten_test.jsonl", help="Test JSONL file")
    parser.add_argument("--model", type=str, default="drishti-intent", help="Ollama model name")
    parser.add_argument("--backend", type=str, default="ollama", choices=["ollama", "mock"], help="Inference backend")
    parser.add_argument("--ollama-url", type=str, default="http://localhost:11434", help="Ollama base URL")
    parser.add_argument("--limit", type=int, default=None, help="Sample limit")
    parser.add_argument("--output-json", type=str, default=None, help="Output metrics path")

    args = parser.parse_args()
    evaluate_drishti(
        test_file=args.test_file,
        model=args.model,
        backend=args.backend,
        ollama_url=args.ollama_url,
        limit=args.limit,
        output_json=args.output_json,
    )


if __name__ == "__main__":
    main()

