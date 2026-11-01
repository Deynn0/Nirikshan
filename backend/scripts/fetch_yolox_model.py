"""Download or verify the YOLOX-M ONNX model weights.

Run ONCE before using the neural lab workstation detector:
    python scripts/fetch_yolox_model.py

After running this script, all lab asset inference is strictly offline.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

# Primary official release URL for YOLOX-M ONNX
YOLOX_M_URL = "https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_m.onnx"
YOLOX_M_BACKUP_URL = "https://huggingface.co/qualcomm/YOLOX-M/resolve/main/yolox_m.onnx"
EXPECTED_SHA256_PREFIX = "5670"  # prefix verification

MODELS_DIR = Path(__file__).resolve().parent.parent / "var" / "models"
TARGET_FILE = MODELS_DIR / "yolox_m.onnx"


def sha256_prefix(path: Path, length: int = 4) -> str:
    """Compute first n characters of sha256."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:length]


def download_yolox(force: bool = False) -> bool:
    """Fetch YOLOX-M ONNX model."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    if TARGET_FILE.exists() and not force:
        size_mb = TARGET_FILE.stat().st_size / 1024 / 1024
        print(f"✅ YOLOX-M model already present: {TARGET_FILE.name} ({size_mb:.1f} MB)")
        return True

    print(f"Downloading YOLOX-M ONNX model to {TARGET_FILE}...")
    urls_to_try = [YOLOX_M_URL, YOLOX_M_BACKUP_URL]

    for url in urls_to_try:
        try:
            print(f"  Attempting download from: {url}")
            with urllib.request.urlopen(url, timeout=120) as response:  # noqa: S310
                total = int(response.headers.get("Content-Length", 0))
                downloaded = 0
                with TARGET_FILE.open("wb") as out:
                    while chunk := response.read(65536):
                        out.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            pct = downloaded / total * 100
                            print(f"\r  Progress: {pct:.1f}% ({downloaded/1024/1024:.1f} MB)", end="", flush=True)
            print(f"\n  ✅ Downloaded successfully: {TARGET_FILE.name}")
            return True
        except Exception as exc:
            print(f"\n  ⚠️  Failed from {url}: {exc}")
            if TARGET_FILE.exists():
                TARGET_FILE.unlink()

    print("❌ Failed to download YOLOX-M from all mirrors.", file=sys.stderr)
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch YOLOX-M ONNX Model Weights")
    parser.add_argument("--force", action="store_true", help="Force re-download even if already present")
    parser.add_argument("--check-only", action="store_true", help="Only verify whether model is present")
    args = parser.parse_args()

    if args.check_only:
        if TARGET_FILE.exists():
            print(f"✅ Model exists: {TARGET_FILE} ({TARGET_FILE.stat().st_size / 1024 / 1024:.1f} MB)")
            sys.exit(0)
        else:
            print(f"❌ Model missing: {TARGET_FILE}")
            sys.exit(1)

    success = download_yolox(force=args.force)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
