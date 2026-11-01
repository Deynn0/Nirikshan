"""Signed QR code verification module.

Features:
- Decodes QR codes using OpenCV (with optional pyzbar fallback).
- Parses QR payload format: {data, signature, key_id}.
- Cryptographically verifies signature using Ed25519 or ECDSA public keys from keyring.
- Returns status: VALID, INVALID, or UNKNOWN_ISSUER.
- Maps verification findings into EvidenceItem adhering to Trust Ladder rules.
- Provides helper to sign payloads for issuance or tests.
"""

from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

import cv2
import numpy as np
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519

from nirikshan.config import settings
from nirikshan.trust.ladder import EvidenceItem, TrustLevel

log = logging.getLogger(__name__)


class QRVerificationStatus(StrEnum):
    """Result of QR signature verification."""

    VALID = "VALID"
    INVALID = "INVALID"
    UNKNOWN_ISSUER = "UNKNOWN_ISSUER"


@dataclass
class KeyringEntry:
    """Public key record in keyring."""

    key_id: str
    algorithm: str  # "Ed25519" or "ECDSA"
    issuer: str
    role: str = "ISSUER_OFFICER"
    curve: str | None = None
    public_key_pem: str = ""
    public_key_obj: Any = None


class Keyring:
    """Manages public keys used for signed QR verification."""

    def __init__(self, keyring_path: Path | None = None) -> None:
        self.keyring_path = keyring_path or settings.keyring_json_path
        self.keys: dict[str, KeyringEntry] = {}
        self._load()

    def _load(self) -> None:
        if not self.keyring_path or not self.keyring_path.exists():
            return
        try:
            with open(self.keyring_path, encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("keys", []):
                self.add_key_from_dict(item)
        except Exception as exc:
            log.warning("Failed to load keyring from %s: %s", self.keyring_path, exc)

    def add_key_from_dict(self, item: dict[str, Any]) -> None:
        key_id = item["key_id"]
        algo = item.get("algorithm", "Ed25519")
        pem = item.get("public_key_pem", "")
        pub_obj = None
        if pem:
            try:
                pub_obj = serialization.load_pem_public_key(pem.encode())
            except Exception as e:
                log.warning("Could not parse PEM for key %s: %s", key_id, e)

        self.keys[key_id] = KeyringEntry(
            key_id=key_id,
            algorithm=algo,
            issuer=item.get("issuer", "Unknown Issuer"),
            role=item.get("role", "ISSUER_OFFICER"),
            curve=item.get("curve"),
            public_key_pem=pem,
            public_key_obj=pub_obj,
        )

    def add_key(self, entry: KeyringEntry) -> None:
        self.keys[entry.key_id] = entry

    def get_key(self, key_id: str) -> KeyringEntry | None:
        return self.keys.get(key_id)


def canonicalize_data(data: Any) -> bytes:
    """Serialize data into deterministic canonical bytes for signing/verifying."""
    if isinstance(data, (dict, list)):
        return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if isinstance(data, bytes):
        return data
    return str(data).encode("utf-8")


def decode_qr_from_image(image_input: bytes | Path | str | np.ndarray) -> list[str]:
    """Decode one or more QR code text payloads from an image."""
    img: np.ndarray | None = None
    if isinstance(image_input, (str, Path)):
        img = cv2.imread(str(image_input))
    elif isinstance(image_input, bytes):
        nparr = np.frombuffer(image_input, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    elif isinstance(image_input, np.ndarray):
        img = image_input

    if img is None:
        return []

    results: list[str] = []

    # 1. Try OpenCV QRCodeDetector detectAndDecode
    detector = cv2.QRCodeDetector()
    try:
        val, _, _ = detector.detectAndDecode(img)
        if val and val.strip():
            results.append(val.strip())
    except Exception:
        pass

    # 2. Try detectAndDecodeMulti
    if not results:
        try:
            ok, decoded_info, _, _ = detector.detectAndDecodeMulti(img)
            if ok and decoded_info:
                for item in decoded_info:
                    if item and item.strip() and item.strip() not in results:
                        results.append(item.strip())
        except Exception:
            pass

    # 3. Try with quiet zone padding + scaling
    if not results:
        try:
            bordered = cv2.copyMakeBorder(img, 30, 30, 30, 30, cv2.BORDER_CONSTANT, value=[255, 255, 255])
            val, _, _ = detector.detectAndDecode(bordered)
            if val and val.strip():
                results.append(val.strip())
            else:
                scaled = cv2.resize(bordered, (0, 0), fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
                val, _, _ = detector.detectAndDecode(scaled)
                if val and val.strip():
                    results.append(val.strip())
                else:
                    gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY) if len(scaled.shape) == 3 else scaled
                    val, _, _ = detector.detectAndDecode(gray)
                    if val and val.strip():
                        results.append(val.strip())
                    else:
                        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
                        val, _, _ = detector.detectAndDecode(thresh)
                        if val and val.strip():
                            results.append(val.strip())
        except Exception:
            pass

    # 4. Try direct grayscale / Otsu on original
    if not results:
        try:
            gray_orig = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
            val, _, _ = detector.detectAndDecode(gray_orig)
            if val and val.strip():
                results.append(val.strip())
            else:
                _, otsu = cv2.threshold(gray_orig, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
                val, _, _ = detector.detectAndDecode(otsu)
                if val and val.strip():
                    results.append(val.strip())
        except Exception:
            pass

    return results


def _decode_sig_bytes(sig_str: str) -> bytes:
    """Decode signature from base64 or hex format."""
    sig_str = sig_str.strip()
    # Try base64 first
    try:
        raw = base64.b64decode(sig_str, validate=True)
        if len(raw) in (64, 70, 71, 72, 73, 74):  # Common Ed25519 and DER ECDSA sizes
            return raw
    except Exception:
        pass

    # Try hex
    try:
        return bytes.fromhex(sig_str)
    except Exception:
        pass

    # Plain base64 decode fallback
    return base64.b64decode(sig_str)


@dataclass
class QRVerificationResult:
    """Result of verifying a signed QR code payload."""

    status: QRVerificationStatus
    key_id: str | None = None
    issuer: str | None = None
    role: str = "UNKNOWN"
    data: Any = None
    is_tampered: bool = False
    details: str = ""
    evidence_item: EvidenceItem | None = None


def verify_qr_payload(
    payload_input: dict[str, Any] | str,
    keyring: Keyring | None = None,
    *,
    source_document_id: str = "doc_unknown",
    source_document_name: str = "document_qr",
) -> QRVerificationResult:
    """Verify signed QR payload format: {data, signature, key_id}.

    Trust Ladder mapping:
    - VALID: TrustLevel.CRYPTOGRAPHIC (Rank 60)
    - INVALID: TrustLevel.STRUCTURAL_FORENSIC (Rank 20), is_tampered = True
    - UNKNOWN_ISSUER: TrustLevel.UNVERIFIED_CLAIM (Rank 0)
    """
    if isinstance(payload_input, str):
        try:
            payload = json.loads(payload_input)
        except Exception:
            return QRVerificationResult(
                status=QRVerificationStatus.INVALID,
                details="Payload is not valid JSON.",
                is_tampered=True,
            )
    else:
        payload = payload_input

    if not isinstance(payload, dict):
        return QRVerificationResult(
            status=QRVerificationStatus.INVALID,
            details="Payload root must be a JSON dictionary.",
            is_tampered=True,
        )

    data = payload.get("data")
    sig_str = payload.get("signature")
    key_id = payload.get("key_id")

    if not key_id or sig_str is None or data is None:
        return QRVerificationResult(
            status=QRVerificationStatus.INVALID,
            key_id=key_id,
            data=data,
            details="Missing required QR payload fields (data, signature, key_id).",
            is_tampered=True,
        )

    kr = keyring or Keyring()
    key_entry = kr.get_key(str(key_id))

    if not key_entry or not key_entry.public_key_obj:
        ev = EvidenceItem(
            evidence_id=f"ev-qr-unknown-{uuid4().hex[:6]}",
            trust_level=TrustLevel.UNVERIFIED_CLAIM,
            source_type="Signed QR Code",
            description=f"Signed QR references unregistered key ID '{key_id}'. Cannot verify authority.",
            raw_value={"key_id": key_id, "data": data},
            source_document_id=source_document_id,
            source_document_name=source_document_name,
            is_self_attested=False,
            is_tampered=False,
            verification_method="SIGNED_QR_UNKNOWN_ISSUER",
        )
        return QRVerificationResult(
            status=QRVerificationStatus.UNKNOWN_ISSUER,
            key_id=key_id,
            data=data,
            details=f"Key ID '{key_id}' not found in public keyring registry.",
            evidence_item=ev,
        )

    # Decode signature
    try:
        sig_bytes = _decode_sig_bytes(str(sig_str))
    except Exception as exc:
        ev = EvidenceItem(
            evidence_id=f"ev-qr-invalid-{uuid4().hex[:6]}",
            trust_level=TrustLevel.STRUCTURAL_FORENSIC,
            source_type="Signed QR Code",
            description=f"Signed QR signature bytes malformed: {exc}",
            raw_value={"key_id": key_id, "data": data},
            source_document_id=source_document_id,
            source_document_name=source_document_name,
            is_self_attested=False,
            is_tampered=True,
            verification_method="SIGNED_QR_CORRUPT",
        )
        return QRVerificationResult(
            status=QRVerificationStatus.INVALID,
            key_id=key_id,
            issuer=key_entry.issuer,
            role=key_entry.role,
            data=data,
            is_tampered=True,
            details=f"Malformed signature encoding: {exc}",
            evidence_item=ev,
        )

    canon_bytes = canonicalize_data(data)
    pub_key = key_entry.public_key_obj
    is_valid = False

    try:
        if isinstance(pub_key, ed25519.Ed25519PublicKey):
            pub_key.verify(sig_bytes, canon_bytes)
            is_valid = True
        elif isinstance(pub_key, ec.EllipticCurvePublicKey):
            pub_key.verify(sig_bytes, canon_bytes, ec.ECDSA(hashes.SHA256()))
            is_valid = True
        else:
            # General public key verify
            pub_key.verify(sig_bytes, canon_bytes)
            is_valid = True
    except InvalidSignature:
        is_valid = False
    except Exception as exc:
        log.debug("Signature check raised exception: %s", exc)
        is_valid = False

    if is_valid:
        ev = EvidenceItem(
            evidence_id=f"ev-qr-valid-{uuid4().hex[:6]}",
            trust_level=TrustLevel.CRYPTOGRAPHIC,
            source_type="Signed QR Code",
            description=(
                f"Valid cryptographic QR endorsement by {key_entry.issuer} "
                f"(Key: {key_id}, Alg: {key_entry.algorithm})."
            ),
            raw_value={
                "status": "VALID",
                "key_id": key_id,
                "issuer": key_entry.issuer,
                "role": key_entry.role,
                "data": data,
            },
            source_document_id=source_document_id,
            source_document_name=source_document_name,
            is_self_attested=False,
            is_tampered=False,
            verification_method=f"SIGNED_QR_{key_entry.algorithm.upper()}",
        )
        return QRVerificationResult(
            status=QRVerificationStatus.VALID,
            key_id=key_id,
            issuer=key_entry.issuer,
            role=key_entry.role,
            data=data,
            is_tampered=False,
            details=f"Cryptographically valid signature from verified issuer '{key_entry.issuer}'.",
            evidence_item=ev,
        )

    # Invalid signature
    ev = EvidenceItem(
        evidence_id=f"ev-qr-invalid-{uuid4().hex[:6]}",
        trust_level=TrustLevel.STRUCTURAL_FORENSIC,
        source_type="Signed QR Code",
        description=(
            f"INVALID cryptographic signature for key '{key_id}' claiming issuer '{key_entry.issuer}'. "
            "Data tampering or forged signature detected."
        ),
        raw_value={
            "status": "INVALID",
            "key_id": key_id,
            "issuer": key_entry.issuer,
            "data": data,
        },
        source_document_id=source_document_id,
        source_document_name=source_document_name,
        is_self_attested=False,
        is_tampered=True,
        verification_method=f"SIGNED_QR_{key_entry.algorithm.upper()}",
    )
    return QRVerificationResult(
        status=QRVerificationStatus.INVALID,
        key_id=key_id,
        issuer=key_entry.issuer,
        role=key_entry.role,
        data=data,
        is_tampered=True,
        details="Signature verification failed. The payload data or signature has been modified.",
        evidence_item=ev,
    )


def sign_qr_payload(
    data: Any,
    private_key: ed25519.Ed25519PrivateKey | ec.EllipticCurvePrivateKey,
    key_id: str,
) -> dict[str, Any]:
    """Helper to produce a valid signed QR payload."""
    canon_bytes = canonicalize_data(data)
    if isinstance(private_key, ed25519.Ed25519PrivateKey):
        sig = private_key.sign(canon_bytes)
    elif isinstance(private_key, ec.EllipticCurvePrivateKey):
        sig = private_key.sign(canon_bytes, ec.ECDSA(hashes.SHA256()))
    else:
        sig = private_key.sign(canon_bytes)

    sig_b64 = base64.b64encode(sig).decode("utf-8")
    return {
        "data": data,
        "signature": sig_b64,
        "key_id": key_id,
    }
