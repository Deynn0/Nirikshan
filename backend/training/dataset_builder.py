"""Synthetic dataset generator for fine-tuning regulatory extraction models.

Generates instruction -> JSON training pairs conforming to AICTE regulatory schemas.
Produces both Alpaca instruction format and ChatML format compatible with TRL SFTTrainer.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

# Domain templates for AICTE regulatory scrutiny
INSTITUTE_NAMES = [
    "Vidyapeeth Institute of Technology",
    "Aryabhata College of Engineering",
    "Kalam Technical Institute",
    "Saraswati Polytechnic Institute",
    "National College of Architecture and Planning",
    "Sahyadri Institute of Technology & Management",
    "Deccan Academy of Technology",
]

LAND_USE_PURPOSES = ["EDUCATIONAL", "INSTITUTIONAL", "ACADEMIC_CAMPUS"]
LOCATION_TYPES = ["Urban", "Rural", "Metro", "Mega City"]
SURVEY_PREFIXES = ["Sy.No.", "Survey No.", "Khasra No.", "Plot No.", "Gat No."]


def generate_synthetic_record(seed: int | None = None) -> dict[str, Any]:
    """Generate a single paired synthetic document and ground-truth extracted JSON."""
    if seed is not None:
        random.seed(seed)

    inst_name = random.choice(INSTITUTE_NAMES)
    location = random.choice(LOCATION_TYPES)
    land_area = round(random.uniform(1.5, 12.0), 2)
    survey_no = f"{random.randint(10, 850)}/{random.randint(1, 9)}{random.choice(['A', 'B', 'C', ''])}"
    survey_label = f"{random.choice(SURVEY_PREFIXES)} {survey_no}"
    fire_year = random.randint(2025, 2028)
    fire_month = f"{random.randint(1, 12):02d}"
    fire_day = f"{random.randint(1, 28):02d}"
    fire_expiry = f"{fire_year}-{fire_month}-{fire_day}"
    workstations = random.choice([30, 60, 90, 120, 150, 180, 240, 300])
    faculty_count = random.randint(15, 60)
    intake = random.choice([120, 180, 240, 300, 360, 480])

    doc_text = (
        f"OFFICIAL SCRUTINY RECORD — {inst_name.upper()}\n"
        f"Location Classification: {location} Region.\n"
        f"Land Title Record: Registered Sale Deed No. {random.randint(1000, 9999)}/{random.randint(2010, 2023)}.\n"
        f"Demarcation: The campus parcel measures {land_area} acres situated at {survey_label}.\n"
        f"The land use is officially demarcated for {random.choice(LAND_USE_PURPOSES)} purposes.\n"
        f"Safety & Compliance: State Fire Services NOC Certificate issued under Ref FS-{random.randint(100, 999)}.\n"
        f"Fire NOC Validity: Valid until {fire_expiry}.\n"
        f"Infrastructure Audit: Computer Laboratory equipped with {workstations} operational workstations.\n"
        f"Academic Intake: Sanctioned annual intake of {intake} students with {faculty_count} appointed full-time faculty members.\n"
    )

    ground_truth = {
        "institution_name": inst_name,
        "location_type": location,
        "land_area_acres": land_area,
        "survey_no": survey_no,
        "fire_noc_expiry_date": fire_expiry,
        "lab_workstation_count": workstations,
        "total_faculty": faculty_count,
        "approved_intake": intake,
    }

    instruction = (
        "Extract structured regulatory fields from the document text into valid JSON with keys: "
        "institution_name, location_type, land_area_acres, survey_no, fire_noc_expiry_date, "
        "lab_workstation_count, total_faculty, approved_intake."
    )

    return {
        "instruction": instruction,
        "input": doc_text,
        "output": json.dumps(ground_truth, indent=2),
        "ground_truth": ground_truth,
        "messages": [
            {
                "role": "system",
                "content": "You are a regulatory document parsing assistant for AICTE scrutiny. Return only valid raw JSON conforming to the requested fields without hallucination.",
            },
            {
                "role": "user",
                "content": f"{instruction}\n\nDOCUMENT TEXT:\n{doc_text}",
            },
            {
                "role": "assistant",
                "content": json.dumps(ground_truth),
            },
        ],
    }


def build_synthetic_dataset(
    num_samples: int = 200,
    val_ratio: float = 0.2,
    output_dir: Path | str = "data",
) -> tuple[Path, Path]:
    """Generate train and validation jsonl files."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    records = [generate_synthetic_record(seed=1000 + i) for i in range(num_samples)]
    random.shuffle(records)

    split_idx = int(num_samples * (1.0 - val_ratio))
    train_records = records[:split_idx]
    val_records = records[split_idx:]

    train_file = out_path / "train.jsonl"
    val_file = out_path / "val.jsonl"

    with train_file.open("w", encoding="utf-8") as f:
        for r in train_records:
            f.write(json.dumps(r) + "\n")

    with val_file.open("w", encoding="utf-8") as f:
        for r in val_records:
            f.write(json.dumps(r) + "\n")

    print(f"Generated {len(train_records)} train samples in {train_file}")
    print(f"Generated {len(val_records)} validation samples in {val_file}")
    return train_file, val_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic Regulatory Dataset Builder")
    parser.add_argument("--num-samples", type=int, default=200, help="Total number of samples to generate")
    parser.add_argument("--val-ratio", type=float, default=0.2, help="Validation set split ratio (default: 0.2)")
    parser.add_argument("--output-dir", type=str, default="data", help="Output directory for jsonl files")
    args = parser.parse_args()

    build_synthetic_dataset(
        num_samples=args.num_samples,
        val_ratio=args.val_ratio,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
