"""Synthetic multilingual dataset generator for Drishti intent classifier.

Generates paired user queries and structured JSON intent classifications across
English, Hindi, and Hinglish.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

from lexicon import INTENTS, INTENT_TEMPLATES

# Ensure stdout handles UTF-8 on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SAMPLE_ENTITIES = {
    "inst": ["Vidyapeeth Institute", "Kalam Technical College", "Aryabhata Engineering College"],
    "noc_no": ["NOC2024881928", "FS-9281-2024", "NOC/2025/1109"],
    "cc_no": ["CC/BHO/4921/24", "OC-2023-882", "BCC/NMM/9912"],
    "area": ["4500", "7200", "12500", "18000"],
    "acres": ["2.5", "5.0", "7.5", "10.0"],
    "location": ["Urban", "Rural", "Metro", "Mega City"],
    "survey_no": ["142/2A", "88/1", "Khasra No. 204"],
    "stamp_val": ["100", "500"],
    "estamp_no": ["IN-DL982187391823A", "IN-MH449102830198H"],
    "app_id": ["APP-2025-48192", "APP/2026/C9921"],
    "txn_id": ["TER25-9921827", "TXN918203810"],
    "amount": ["100,000", "150,000", "200,000"],
    "udin": ["24103362PNATEG4891", "25190333TVRQVU7220"],
    "fin_yr": ["2023-2024", "2024-2025"],
    "cert_no": ["STR/PUN/882/2024", "STR/LKO/401/2025"],
    "intake": ["180", "240", "300", "360", "480"],
    "faculty": ["15", "20", "24", "30"],
}


def render_query(template: str) -> tuple[str, dict[str, str]]:
    """Fill placeholder slots with realistic sample entities."""
    slots: dict[str, str] = {}
    rendered = template
    for key, values in SAMPLE_ENTITIES.items():
        placeholder = f"{{{key}}}"
        if placeholder in rendered:
            chosen = random.choice(values)
            rendered = rendered.replace(placeholder, chosen)
            slots[key] = chosen
    return rendered, slots


def generate_sample(intent: str, lang: str | None = None) -> dict[str, Any]:
    """Generate a single intent classification record in ChatML format."""
    lang_options = list(INTENT_TEMPLATES[intent].keys())
    chosen_lang = lang if lang in lang_options else random.choice(lang_options)
    templates = INTENT_TEMPLATES[intent][chosen_lang]
    tmpl = random.choice(templates)

    query_text, slots = render_query(tmpl)

    target_json = {
        "intent": intent,
        "confidence": 0.99 if intent != "out_of_scope" else 0.95,
        "entity_slots": slots,
    }

    system_msg = (
        "You are Drishti, an AICTE regulatory scrutiny intent classifier. "
        "Classify the user's scrutiny query into valid JSON with keys: "
        "intent, confidence, entity_slots. Reply with JSON only."
    )

    return {
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": query_text},
            {"role": "assistant", "content": json.dumps(target_json)},
        ],
        "meta": {
            "intent": intent,
            "language": chosen_lang,
            "target": target_json,
        },
    }


def generate_dataset(
    output_dir: str | Path = ".",
    num_train: int = 1200,
    num_val: int = 150,
    seed: int = 42,
) -> None:
    """Generate train and val jsonl splits for Drishti."""
    random.seed(seed)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    train_path = out_dir / "train.jsonl"
    val_path = out_dir / "val.jsonl"

    print(f"Generating {num_train} train and {num_val} val intent samples...")

    with train_path.open("w", encoding="utf-8") as f:
        for i in range(num_train):
            intent = INTENTS[i % len(INTENTS)]
            sample = generate_sample(intent)
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    with val_path.open("w", encoding="utf-8") as f:
        for i in range(num_val):
            intent = INTENTS[i % len(INTENTS)]
            sample = generate_sample(intent)
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    print(f"Drishti intent dataset saved to: {out_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Drishti Intent Dataset")
    parser.add_argument("--output-dir", type=str, default=".", help="Output directory")
    parser.add_argument("--num-train", type=int, default=1200, help="Train samples")
    parser.add_argument("--num-val", type=int, default=150, help="Val samples")
    parser.add_argument("--seed", type=int, default=42, help="Seed")

    args = parser.parse_args()
    generate_dataset(output_dir=args.output_dir, num_train=args.num_train, num_val=args.num_val, seed=args.seed)


if __name__ == "__main__":
    main()

