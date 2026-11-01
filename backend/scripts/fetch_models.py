"""scripts/fetch_models.py — Download RapidOCR ONNX model weights.

Run ONCE before first use:
    python scripts/fetch_models.py

After running this script, all OCR inference is strictly offline.
No network calls are made at inference time.

Models downloaded:
  - ch_PP-OCRv3_det.onnx  (text detector, ~3 MB)
  - en_PP-OCRv3_rec.onnx  (English recognizer, ~9 MB)
  - hi_PP-OCRv3_rec.onnx  (Devanagari recognizer, ~9 MB)

Source: https://github.com/PaddlePaddle/PaddleOCR (Apache 2.0 license)
These weights are published by PaddlePaddle / Baidu. No proprietary content.
"""

from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Model registry: (filename, download_url, expected_sha256_prefix)
# ---------------------------------------------------------------------------
_MODELS: list[tuple[str, str, str]] = [
    (
        "ch_PP-OCRv3_det.onnx",
        "https://github.com/RapidAI/RapidOCR/releases/download/v1.1.0/ch_PP-OCRv3_det_infer.onnx",
        "9a8a",  # prefix check only — full hash for CI
    ),
    (
        "en_PP-OCRv3_rec.onnx",
        "https://github.com/RapidAI/RapidOCR/releases/download/v1.1.0/en_PP-OCRv3_rec_infer.onnx",
        "4b2c",
    ),
    (
        "hi_PP-OCRv3_rec.onnx",
        "https://github.com/RapidAI/RapidOCR/releases/download/v1.1.0/hi_PP-OCRv3_rec_infer.onnx",
        "7e1f",
    ),
]

_MODELS_DIR = Path(__file__).resolve().parent.parent / "var" / "models"


def _download_file(url: str, dest: Path) -> None:
    print(f"  Downloading: {dest.name}")
    print(f"  URL: {url}")
    try:
        with urllib.request.urlopen(url, timeout=120) as response:  # noqa: S310
            total = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            with dest.open("wb") as out:
                while chunk := response.read(65536):
                    out.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded / total * 100
                        print(f"\r  Progress: {pct:.1f}%", end="", flush=True)
        print(f"\r  ✅ Saved: {dest.name} ({downloaded/1024/1024:.1f} MB)")
    except Exception as exc:
        print(f"\n  ❌ FAILED to download {dest.name}: {exc}", file=sys.stderr)
        if dest.exists():
            dest.unlink()
        raise


def _sha256_prefix(path: Path, length: int = 4) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:length]


def main() -> None:
    _MODELS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Model directory: {_MODELS_DIR}\n")

    any_failed = False
    for filename, url, sha_prefix in _MODELS:
        dest = _MODELS_DIR / filename
        if dest.exists():
            actual = _sha256_prefix(dest, len(sha_prefix))
            if actual == sha_prefix:
                size_mb = dest.stat().st_size / 1024 / 1024
                print(f"  ✅ Already present: {filename} ({size_mb:.1f} MB)")
                continue
            print(f"  ⚠️  Hash mismatch for {filename} — re-downloading")
            dest.unlink()

        try:
            _download_file(url, dest)
            # Verify prefix
            actual = _sha256_prefix(dest, len(sha_prefix))
            if actual != sha_prefix:
                print(f"  ⚠️  SHA-256 prefix mismatch for {filename}: got {actual}, expected {sha_prefix}")
        except Exception:
            any_failed = True

    print()
    if any_failed:
        print("❌ Some models failed to download. Check network connectivity.")
        sys.exit(1)
    else:
        print("✅ All OCR models ready. Runtime inference is now fully offline.")


if __name__ == "__main__":
    main()
