"""LoRA Fine-Tuning Script using PEFT and TRL for Qwen 1.7B / 4B models.

Advisory ML Layer (Trust Ladder: Model).
DO NOT RUN TRAINING AUTOMATICALLY. Requires explicit confirmation via CLI flag.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def train_lora(
    model_id: str = "Qwen/Qwen2.5-1.5B-Instruct",
    dataset_path: str = "data/train.jsonl",
    val_dataset_path: str | None = "data/val.jsonl",
    output_dir: str = "lora_qwen_regulatory",
    num_epochs: int = 3,
    batch_size: int = 2,
    gradient_accumulation_steps: int = 4,
    learning_rate: float = 2e-4,
    lora_r: int = 16,
    lora_alpha: int = 32,
    lora_dropout: float = 0.05,
    use_4bit: bool = False,
) -> None:
    """Execute LoRA / QLoRA training using PEFT and TRL SFTTrainer.

    NOTE: Fine-tuned model output remains strictly TrustLevel.MODEL (Advisory Only).
    """
    try:
        import torch
        from datasets import load_dataset
        from peft import LoraConfig, TaskType
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
            TrainingArguments,
        )
        from trl import SFTTrainer
    except ImportError as exc:
        print(
            f"ERROR: Missing training dependencies: {exc}\n"
            "Please install the training stack:\n"
            "    pip install torch transformers peft trl datasets accelerate bitsandbytes\n",
            file=sys.stderr,
        )
        sys.exit(1)

    print("================================================================")
    print("      NIRIKSHAN REGULATORY FINE-TUNING SCAFFOLD (LoRA / TRL)     ")
    print("================================================================")
    print(f"Base Model:             {model_id}")
    print(f"Dataset Path:           {dataset_path}")
    print(f"Output Directory:       {output_dir}")
    print(f"LoRA Rank (r):          {lora_r}, Alpha: {lora_alpha}")
    print(f"Batch Size:             {batch_size} (Grad Accum: {gradient_accumulation_steps})")
    print(f"Learning Rate:          {learning_rate}")
    print(f"Epochs:                 {num_epochs}")
    print(f"4-bit Quantization:     {use_4bit}")
    print(f"CUDA Available:         {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"Device Name:            {torch.cuda.get_device_name(0)}")
        print(f"VRAM Available:         {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    print("================================================================\n")

    # 1. Load Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 2. Quantization / Model Loading
    quant_config = None
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    if use_4bit and torch.cuda.is_available():
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=quant_config,
        torch_dtype=torch_dtype,
        device_map="auto" if torch.cuda.is_available() else None,
        trust_remote_code=True,
    )

    # 3. LoRA Configuration for Qwen
    # Qwen attention + MLP projections: q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj
    peft_config = LoraConfig(
        r=lora_r,
        lora_alpha=lora_alpha,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=lora_dropout,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )

    # 4. Load Datasets
    data_files = {"train": dataset_path}
    if val_dataset_path and Path(val_dataset_path).exists():
        data_files["validation"] = val_dataset_path
    dataset = load_dataset("json", data_files=data_files)

    # 5. Training Arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        learning_rate=learning_rate,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        logging_steps=10,
        save_strategy="epoch",
        evaluation_strategy="epoch" if "validation" in dataset else "no",
        fp16=torch.cuda.is_available(),
        bf16=False,
        save_total_limit=2,
        report_to="none",
    )

    # 6. Initialize SFTTrainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset["train"],
        eval_dataset=dataset.get("validation"),
        peft_config=peft_config,
        tokenizer=tokenizer,
        args=training_args,
        max_seq_length=2048,
    )

    print("🚀 Starting fine-tuning...")
    trainer.train()

    # 7. Save Adapter
    final_adapter_dir = Path(output_dir) / "final_adapter"
    trainer.model.save_pretrained(str(final_adapter_dir))
    tokenizer.save_pretrained(str(final_adapter_dir))
    print(f"✅ Training complete. LoRA adapter saved to: {final_adapter_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Qwen LoRA Training with PEFT and TRL")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-1.5B-Instruct", help="Base model identifier")
    parser.add_argument("--dataset", type=str, default="data/train.jsonl", help="Path to train.jsonl")
    parser.add_argument("--val-dataset", type=str, default="data/val.jsonl", help="Path to val.jsonl")
    parser.add_argument("--output-dir", type=str, default="lora_qwen_regulatory", help="Output directory")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=2, help="Per device batch size")
    parser.add_argument("--learning-rate", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--lora-r", type=int, default=16, help="LoRA rank dimension")
    parser.add_argument("--4bit", dest="use_4bit", action="store_true", help="Enable 4-bit QLoRA")
    parser.add_argument(
        "--confirm-training",
        action="store_true",
        help="SAFETY FLAG: Explicitly confirm training execution. Training is NOT run automatically.",
    )
    args = parser.parse_args()

    if not args.confirm_training:
        print(
            "⚠️  SAFETY HALT: Training script was called without '--confirm-training'.\n"
            "As specified in regulatory guidelines, training must NOT run automatically.\n"
            "To launch training, pass '--confirm-training':\n"
            f"    python {Path(__file__).name} --confirm-training --model {args.model}\n"
        )
        sys.exit(0)

    train_lora(
        model_id=args.model,
        dataset_path=args.dataset,
        val_dataset_path=args.val_dataset,
        output_dir=args.output_dir,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        lora_r=args.lora_r,
        use_4bit=args.use_4bit,
    )


if __name__ == "__main__":
    main()
