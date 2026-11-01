# Nirikshan Advisory ML Fine-Tuning Scaffold

> **TRUST LADDER LEVEL**: **MODEL** (Rank 10 — Advisory Only)  
> In accordance with AICTE Scrutiny Core Principle 1, model extractions are strictly **advisory** and cannot independently issue a decisive `PASS` or `FAIL` without human verification or higher-tier documentary evidence.

This directory provides the scaffold for fine-tuning compact local language models (specifically **Qwen 2.5 1.5B / Qwen 2.5 3B / Qwen 3 4B**) to perform structured, hallucination-resistant regulatory field extraction from untrusted OCR and text layers.

---

## 1. Hardware & System Requirements

### GPU Requirements (Recommended for Training)

| Model Target | Fine-Tuning Mode | Precision | Minimum VRAM | Recommended VRAM | Recommended GPUs |
|:---|:---|:---|:---|:---|:---|
| **Qwen 1.5B / 1.7B** | QLoRA (4-bit) | NF4 / FP16 | **6 GB** | 8 GB | RTX 3060, RTX 4060, T4, RTX 3070 |
| **Qwen 1.5B / 1.7B** | Standard LoRA | FP16 / BF16 | **10 GB** | 12 GB | RTX 3060 12GB, RTX 4070, V100 |
| **Qwen 3B / 4B** | QLoRA (4-bit) | NF4 / FP16 | **8 GB** | 12 GB | RTX 3060 12GB, RTX 4070, RTX 3080 |
| **Qwen 3B / 4B** | Standard LoRA | FP16 / BF16 | **16 GB** | 24 GB | RTX 3090, RTX 4090, A10, A5000 |

### CPU & RAM Requirements (Alternative / Local Scrutiny)

- **System RAM**:
  - Minimum: **16 GB** (for 1.5B / 1.7B QLoRA / CPU inference)
  - Recommended: **32 GB** (for 3B / 4B models)
- **CPU Cores**: 8+ physical cores (Intel Core i7/i9, AMD Ryzen 7/9, Apple Silicon M1/M2/M3 Pro/Max)
- **Storage**: ~15 GB free NVMe disk space for checkpoints, base weights, and datasets.
- *Note*: CPU-only training is technically possible with Hugging Face Accelerate, but training speeds will be ~15-20x slower than on CUDA GPUs. Local CPU deployment is primarily intended for quantized **Ollama / llama.cpp inference** at runtime.

---

## 2. Dependencies Installation

To set up the training environment (isolated from the core production backend):

```bash
pip install torch transformers peft trl datasets accelerate bitsandbytes rapidfuzz
```

---

## 3. Workflow Steps

### Step 1: Generate Synthetic Regulatory Dataset

The dataset builder generates paired regulatory document passages and ground-truth JSON extractions based on AICTE Approval Process Handbook (APH) clauses:

```bash
python dataset_builder.py --num-samples 500 --val-ratio 0.2 --output-dir data/
```

This creates:
- `data/train.jsonl` (400 samples)
- `data/val.jsonl` (100 samples)

Each sample includes both Alpaca-style `{instruction, input, output}` and ChatML-style `{messages: [...]}` formats.

### Step 2: Run LoRA Fine-Tuning

> **IMPORTANT**: Training does **NOT** run automatically. To prevent accidental resource consumption, you must pass the `--confirm-training` flag.

```bash
# Example 1: 4-bit QLoRA on a consumer GPU (8GB+ VRAM)
python train_lora.py \
    --confirm-training \
    --model Qwen/Qwen2.5-1.5B-Instruct \
    --dataset data/train.jsonl \
    --val-dataset data/val.jsonl \
    --output-dir lora_qwen_1.5b_regulatory \
    --epochs 3 \
    --batch-size 2 \
    --4bit

# Example 2: Qwen 3B / 4B LoRA (16GB+ VRAM)
python train_lora.py \
    --confirm-training \
    --model Qwen/Qwen2.5-3B-Instruct \
    --dataset data/train.jsonl \
    --val-dataset data/val.jsonl \
    --output-dir lora_qwen_3b_regulatory \
    --epochs 3 \
    --batch-size 4
```

### Step 3: Evaluate Field Exact Match & Grounding Rate

The evaluation script verifies that the fine-tuned model extracts exact regulatory fields and does **not** hallucinate values absent from the document:

```bash
python evaluate.py \
    --predictions data/eval_predictions.jsonl \
    --output-json eval_metrics.json \
    --threshold 0.85
```

The script reports:
1. **Field-Level Exact Match (EM)**: Proportion of extracted fields that match ground truth exactly.
2. **Document Grounding Rate**: Proportion of extracted fields whose values physically exist in the source document text layer.
3. **Hallucination Rate**: `1.0 - Grounding Rate`. In Nirikshan, ungrounded fields are discarded and logged as `"hallucination_rejected"`.

---

## 4. Serving Fine-Tuned Weights in Ollama

Once the LoRA adapter is trained and merged:

```bash
# 1. Create a Modelfile
cat <<EOF > Modelfile
FROM qwen2.5:1.5b
ADAPTER ./lora_qwen_1.5b_regulatory/final_adapter
PARAMETER temperature 0.1
PARAMETER top_p 0.9
EOF

# 2. Register with Ollama
ollama create qwen-aicte-advisory -f Modelfile

# 3. Configure in Nirikshan
# Set NIRIKSHAN_OLLAMA_MODEL=qwen-aicte-advisory in .env
```
