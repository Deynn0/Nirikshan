"""Cryptographic salted hashing and perceptual distance utilities for fraud graph.

Ensures Aadhaar and PAN numbers are NEVER stored or transmitted in plaintext.
Only cryptographically salted HMAC-SHA256 hashes are persisted.
"""

from __future__ import annotations

import hashlib
import hmac
import re

from nirikshan.config import settings

try:
    import imagehash
    _HAS_IMAGEHASH = True
except ImportError:  # pragma: no cover
    _HAS_IMAGEHASH = False

# Regex patterns for validation & normalization
_RE_AADHAAR = re.compile(r"^\d{12}$")
_RE_PAN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


def normalize_identity_id(raw_id: str) -> str:
    """Normalize Aadhaar or PAN string by stripping whitespace and hyphens.

    Converts to uppercase.
    """
    if not raw_id:
        return ""
    return re.sub(r"[\s\-\.]", "", str(raw_id).strip().upper())


def hash_salted_identity(raw_id: str, salt: str | None = None) -> str:
    """Compute HMAC-SHA256 salted hash of an identity token (Aadhaar, PAN).

    CRITICAL PRIVACY GUARANTEE:
    Raw identity numbers (Aadhaar/PAN) MUST NEVER be stored in the database,
    memory logs, or graph elements. Only deterministic salted hashes are stored,
    which allow identical identities across institutions to be matched without
    revealing plaintext PII.
    """
    clean = normalize_identity_id(raw_id)
    if not clean:
        raise ValueError("Cannot hash empty or invalid identity token.")

    effective_salt = salt if salt is not None else settings.fraud_salt
    if not effective_salt:
        effective_salt = "nirikshan-default-airgap-salt-2024"

    return hmac.new(
        effective_salt.encode("utf-8"),
        clean.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def mask_identity_label(raw_id: str) -> str:
    """Generate a sanitized visual mask (e.g. 'XXXX-XXXX-1234') for UI labeling only.

    Raw full IDs must never be exposed.
    """
    clean = normalize_identity_id(raw_id)
    if len(clean) == 12:  # Aadhaar
        return f"XXXX-XXXX-{clean[-4:]}"
    if len(clean) == 10:  # PAN
        return f"XXXXXX{clean[-4:]}"
    if len(clean) > 4:
        return f"{'*' * (len(clean) - 4)}{clean[-4:]}"
    return "XXXX"


def hamming_distance(hash1: str | None, hash2: str | None) -> int:
    """Compute bitwise Hamming distance between two perceptual hash hex strings.

    Lower distance indicates visual similarity (0 = bitwise identical).
    """
    if not hash1 or not hash2:
        return 64  # Maximum difference for 64-bit hash

    h1_str = hash1.strip().lower()
    h2_str = hash2.strip().lower()

    if h1_str == h2_str:
        return 0

    if _HAS_IMAGEHASH:
        try:
            return int(imagehash.hex_to_hash(h1_str) - imagehash.hex_to_hash(h2_str))
        except Exception:
            pass

    # Pure Python bitwise fallback
    try:
        val1 = int(h1_str, 16)
        val2 = int(h2_str, 16)
        return bin(val1 ^ val2).count("1")
    except ValueError:
        return 64
